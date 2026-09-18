from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.forms import modelform_factory
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import VeiculoForm
from .models import Motorista, Reserva, Veiculo


def criar_reserva(veiculo=None, **alteracoes):
    dados = {
        "solicitante": "Pessoa de teste", "setor": "Operações", "atividade": "Reunião",
        "origem": "Portaria", "destino": "Sede", "data": timezone.localdate() + timedelta(days=2),
        "horario_saida": "08:00", "horario_retorno": "10:00", "quantidade_passageiros": 4,
        "veiculo": veiculo,
    }
    dados.update(alteracoes)
    return Reserva.objects.create(**dados)


class VeiculoModelTests(TestCase):
    def test_capacidades_calculadas_no_servidor(self):
        for categoria, capacidade in Veiculo.CAPACIDADES.items():
            with self.subTest(categoria=categoria):
                v = Veiculo.objects.create(codigo=categoria, categoria=categoria, capacidade=999)
                v.refresh_from_db()
                self.assertEqual(v.capacidade, capacidade)

    def test_categoria_invalida_e_rejeitada(self):
        with self.assertRaises(ValidationError):
            Veiculo.objects.create(codigo="VL-01", categoria="CAMINHAO")

    def test_codigo_normalizado_e_unico(self):
        v = Veiculo.objects.create(codigo=" vl-01 ", categoria="LEVE")
        self.assertEqual(v.codigo, "VL-01")
        with self.assertRaises(ValidationError):
            Veiculo.objects.create(codigo="vl-01", categoria="LEVE")

    def test_formulario_nao_exige_capacidade(self):
        form = VeiculoForm({"codigo": "VL-01", "categoria": "LEVE", "ativo": "on", "capacidade": "500"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().capacidade, 4)

    def test_categoria_recalculada_em_save_parcial(self):
        v = Veiculo.objects.create(codigo="VL-01", categoria="LEVE")
        v.categoria = "COLETIVO"
        v.save(update_fields=["categoria"])
        v.refresh_from_db()
        self.assertEqual(v.capacidade, 18)

    def test_categoria_protegida_se_ha_reserva(self):
        v = Veiculo.objects.create(codigo="VC-01", categoria="COLETIVO")
        criar_reserva(v)
        v.categoria = "LEVE"
        with self.assertRaises(ValidationError):
            v.save()

    def test_desativacao_bloqueada_por_reserva_futura(self):
        v = Veiculo.objects.create(codigo="VL-01", categoria="LEVE")
        criar_reserva(v)
        v.ativo = False
        with self.assertRaises(ValidationError):
            v.save()

    def test_desativacao_permitida_com_apenas_historico(self):
        v = Veiculo.objects.create(codigo="VL-01", categoria="LEVE")
        r = criar_reserva(v)
        with patch("reservas.models.timezone.localtime", return_value=timezone.now() + timedelta(days=5)):
            v.ativo = False
            v.save()
        self.assertTrue(Reserva.objects.filter(pk=r.pk).exists())

    def test_exclusao_protegida(self):
        v = Veiculo.objects.create(codigo="VL-01", categoria="LEVE")
        criar_reserva(v)
        with self.assertRaises(ProtectedError):
            v.delete()

    def test_constraint_no_banco_impede_capacidade_incoerente(self):
        v = Veiculo.objects.create(codigo="VL-01", categoria="LEVE")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Veiculo.objects.filter(pk=v.pk).update(capacidade=18)


class ReservaModelTests(TestCase):
    def setUp(self):
        self.leve = Veiculo.objects.create(codigo="VL-01", categoria="LEVE")
        self.coletivo = Veiculo.objects.create(codigo="VC-01", categoria="COLETIVO")
        self.motorista = Motorista.objects.create(nome="Motorista de teste", matricula="TESTE-01", cnh="TESTE-CNH")

    def test_veiculo_e_motorista_podem_ser_atribuidos_depois(self):
        self.assertIsNone(criar_reserva().veiculo_id)

    def test_passageiros_fora_do_limite(self):
        for n in [0, 19, -1]:
            with self.subTest(n=n), self.assertRaises(ValidationError):
                criar_reserva(quantidade_passageiros=n)

    def test_coletivo_aceita_18(self):
        self.assertIsNotNone(criar_reserva(self.coletivo, quantidade_passageiros=18).pk)

    def test_leve_rejeita_5(self):
        with self.assertRaises(ValidationError):
            criar_reserva(self.leve, quantidade_passageiros=5)

    def test_data_no_passado(self):
        with self.assertRaises(ValidationError):
            criar_reserva(data=timezone.localdate() - timedelta(days=1))

    def test_retorno_igual_ou_anterior(self):
        for horario in ["07:00", "08:00"]:
            with self.subTest(horario=horario), self.assertRaises(ValidationError):
                criar_reserva(horario_retorno=horario)

    def test_sobreposicoes_do_veiculo(self):
        criar_reserva(self.leve)
        for saida, retorno in [("09:00", "11:00"), ("07:00", "09:00"), ("08:30", "09:00"), ("07:00", "11:00"), ("08:00", "10:00")]:
            with self.subTest(saida=saida, retorno=retorno), self.assertRaises(ValidationError):
                criar_reserva(self.leve, horario_saida=saida, horario_retorno=retorno)

    def test_intervalo_completo_de_reserva_nao_deve_sobrepor(self):
        criar_reserva(self.leve, horario_saida="08:00", horario_retorno="14:00")
        with self.assertRaises(ValidationError):
            criar_reserva(self.leve, horario_saida="13:30", horario_retorno="15:00")

    def test_horarios_adjacentes_sao_permitidos(self):
        criar_reserva(self.leve)
        criar_reserva(self.leve, horario_saida="10:00", horario_retorno="12:00")
        criar_reserva(self.leve, horario_saida="06:00", horario_retorno="08:00")
        self.assertEqual(Reserva.objects.count(), 3)

    def test_edicao_nao_conflita_consigo(self):
        reserva = criar_reserva(self.leve)
        reserva.observacoes = "Alteração descritiva"
        reserva.save()
        self.assertEqual(Reserva.objects.count(), 1)

    def test_conflito_de_motorista_com_veiculos_diferentes(self):
        criar_reserva(self.leve, motorista=self.motorista)
        with self.assertRaises(ValidationError):
            criar_reserva(self.coletivo, motorista=self.motorista)

    def test_mesmo_horario_com_recursos_diferentes(self):
        criar_reserva(self.leve)
        criar_reserva(self.coletivo)
        self.assertEqual(Reserva.objects.count(), 2)

    def test_recurso_inativo(self):
        self.leve.ativo = False
        self.leve.save()
        self.motorista.ativo = False
        self.motorista.save()
        with self.assertRaises(ValidationError):
            criar_reserva(self.leve)
        with self.assertRaises(ValidationError):
            criar_reserva(motorista=self.motorista)

    def test_motorista_com_viagem_futura_nao_pode_ser_desativado(self):
        criar_reserva(self.leve, motorista=self.motorista)
        self.motorista.ativo = False
        with self.assertRaises(ValidationError):
            self.motorista.save()

    def test_reserva_historica_permite_apenas_edicao_descritiva(self):
        reserva = criar_reserva(self.leve)
        futuro = timezone.localdate() + timedelta(days=4)
        with patch("reservas.models.timezone.localdate", return_value=futuro):
            reserva.observacoes = "Viagem concluída"
            reserva.save()
            reserva.quantidade_passageiros = 3
            with self.assertRaises(ValidationError):
                reserva.save()

    def test_fk_inexistente_retorna_validacao(self):
        with self.assertRaises(ValidationError):
            criar_reserva(veiculo_id=999999)

    def test_campos_incompletos_no_modelform_nao_causam_500(self):
        form_class = modelform_factory(Reserva, fields="__all__")
        form = form_class({"quantidade_passageiros": "abc", "data": "errado", "horario_saida": "errado"})
        self.assertFalse(form.is_valid())
        self.assertIn("data", form.errors)


class VeiculoViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(username="qa", password="Teste-local-somente-123")
        self.client.force_login(self.user)
        self.veiculo = Veiculo.objects.create(codigo="VL-01", categoria="LEVE")
        self.novo = {"codigo": "VC-02", "categoria": "COLETIVO", "ativo": "on"}

    def url(self, nome):
        args = [] if nome in ("lista", "cadastrar") else [self.veiculo.pk]
        return reverse("reservas:veiculo_" + nome, args=args)

    def test_anonimo_precisa_login_em_todas_as_rotas(self):
        self.client.logout()
        for nome in ("lista", "cadastrar", "detalhe", "editar", "desativar", "excluir"):
            for metodo in (self.client.get, self.client.post):
                with self.subTest(nome=nome, metodo=metodo.__name__):
                    resposta = metodo(self.url(nome))
                    self.assertEqual(resposta.status_code, 302)
                    self.assertIn(reverse("entrar"), resposta.url)

    def test_sem_permissao_recebe_403(self):
        u = get_user_model().objects.create_user(username="sem-permissoes")
        self.client.force_login(u)
        for nome in ("lista", "cadastrar", "detalhe", "editar", "desativar", "excluir"):
            with self.subTest(nome=nome):
                self.assertEqual(self.client.get(self.url(nome)).status_code, 403)
                self.assertEqual(self.client.post(self.url(nome), {"confirmar": "sim"}).status_code, 403)

    def test_perfil_leitor_nao_pode_mutar(self):
        u = get_user_model().objects.create_user(username="leitor")
        u.user_permissions.add(Permission.objects.get(content_type__app_label="reservas", codename="view_veiculo"))
        self.client.force_login(u)
        self.assertEqual(self.client.get(self.url("lista")).status_code, 200)
        self.assertNotContains(self.client.get(self.url("lista")), "Cadastrar veículo")
        for nome in ("cadastrar", "editar", "desativar", "excluir"):
            with self.subTest(nome=nome):
                self.assertEqual(self.client.post(self.url(nome), self.novo).status_code, 403)

    def test_paginas_get_renderizam(self):
        for nome in ("lista", "cadastrar", "detalhe", "editar", "desativar", "excluir"):
            with self.subTest(nome=nome):
                self.assertEqual(self.client.get(self.url(nome)).status_code, 200)

    def test_cadastro_persiste_e_exibe_mensagem(self):
        response = self.client.post(self.url("cadastrar"), self.novo, follow=True)
        self.assertContains(response, "Veículo cadastrado com sucesso.")
        self.assertEqual(Veiculo.objects.get(codigo="VC-02").capacidade, 18)

    def test_edicao_persiste(self):
        self.client.post(self.url("editar"), self.novo)
        self.veiculo.refresh_from_db()
        self.assertEqual(self.veiculo.codigo, "VC-02")
        self.assertEqual(self.veiculo.capacidade, 18)

    def test_codigo_duplicado_mostra_erro(self):
        response = self.client.post(self.url("cadastrar"), {**self.novo, "codigo": " vl-01 "})
        self.assertContains(response, "Já existe um veículo com este código.")
        self.assertEqual(Veiculo.objects.count(), 1)

    def test_campos_vazios_mostram_erros(self):
        response = self.client.post(self.url("cadastrar"), {})
        self.assertContains(response, "Informe o código do veículo.")
        self.assertContains(response, "Selecione uma categoria.")

    def test_categoria_invalida_nao_salva(self):
        response = self.client.post(self.url("cadastrar"), {**self.novo, "categoria": "INVALIDA"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Veiculo.objects.count(), 1)

    def test_get_nunca_exclui_nem_desativa(self):
        self.client.get(self.url("desativar"))
        self.client.get(self.url("excluir"))
        self.veiculo.refresh_from_db()
        self.assertTrue(self.veiculo.ativo)

    def test_post_sem_confirmacao_nao_muta(self):
        for nome in ("desativar", "excluir"):
            self.client.post(self.url(nome))
        self.veiculo.refresh_from_db()
        self.assertTrue(self.veiculo.ativo)

    def test_desativar_e_reativar(self):
        response = self.client.post(self.url("desativar"), {"confirmar": "sim"}, follow=True)
        self.assertContains(response, "Veículo desativado.")
        self.veiculo.refresh_from_db()
        self.assertFalse(self.veiculo.ativo)
        self.client.post(self.url("editar"), {"codigo": "VL-01", "categoria": "LEVE", "ativo": "on"})
        self.veiculo.refresh_from_db()
        self.assertTrue(self.veiculo.ativo)

    def test_desativacao_com_reserva_futura_mostra_erro(self):
        criar_reserva(self.veiculo)
        response = self.client.post(self.url("desativar"), {"confirmar": "sim"})
        self.assertContains(response, "Há reservas em andamento ou futuras.")
        self.veiculo.refresh_from_db()
        self.assertTrue(self.veiculo.ativo)

    def test_editar_nao_contorna_bloqueio_de_desativacao(self):
        criar_reserva(self.veiculo)
        response = self.client.post(self.url("editar"), {"codigo": "VL-01", "categoria": "LEVE"})
        self.assertContains(response, "Há reservas em andamento ou futuras.")
        self.veiculo.refresh_from_db()
        self.assertTrue(self.veiculo.ativo)

    def test_exclusao_real_sem_reserva(self):
        response = self.client.post(self.url("excluir"), {"confirmar": "sim"}, follow=True)
        self.assertContains(response, "Veículo excluído com sucesso.")
        self.assertFalse(Veiculo.objects.filter(pk=self.veiculo.pk).exists())

    def test_exclusao_protegida_com_reserva(self):
        reserva = criar_reserva(self.veiculo)
        response = self.client.post(self.url("excluir"), {"confirmar": "sim"})
        self.assertContains(response, "não pode ser excluído")
        self.assertTrue(Veiculo.objects.filter(pk=self.veiculo.pk).exists())
        self.assertTrue(Reserva.objects.filter(pk=reserva.pk).exists())

    def test_filtros_e_paginacao_preservados(self):
        for i in range(12):
            Veiculo.objects.create(codigo=f"BUS-{i:02}", categoria="COLETIVO")
        response = self.client.get(self.url("lista"), {"q": "BUS", "categoria": "COLETIVO", "situacao": "ativo"})
        self.assertEqual(response.context["pagina"].paginator.count, 12)
        self.assertContains(response, "q=BUS&amp;categoria=COLETIVO&amp;situacao=ativo&amp;page=2")
        response = self.client.get(self.url("lista"), {"page": "abc"})
        self.assertEqual(response.status_code, 200)

    def test_lista_vazia_com_filtro(self):
        self.assertContains(self.client.get(self.url("lista"), {"q": "inexistente"}), "Nenhum veículo encontrado")

    def test_404_para_veiculo_inexistente(self):
        response = self.client.get(reverse("reservas:veiculo_detalhe", args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_csrf_necessario(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url("cadastrar"), self.novo).status_code, 403)
        self.assertEqual(client.post(self.url("excluir"), {"confirmar": "sim"}).status_code, 403)

    def test_login_logout_e_redirecionamento_seguro(self):
        self.client.logout()
        response = self.client.post(reverse("entrar"), {"username": "qa", "password": "Teste-local-somente-123", "next": "https://example.com/"})
        self.assertRedirects(response, reverse("reservas:veiculo_lista"))
        self.assertEqual(self.client.get(reverse("sair")).status_code, 405)
        self.client.post(reverse("sair"))
        self.assertEqual(self.client.get(self.url("lista")).status_code, 302)

    def test_html_carrega_css_js_e_viewport(self):
        response = self.client.get(self.url("cadastrar"))
        for trecho in ("reservas/css/app.css", "reservas/js/app.js", 'name="viewport"', 'name="csrfmiddlewaretoken"', 'id="capacidades"'):
            self.assertContains(response, trecho)

    def test_admin_reserva_dados_invalidos_nao_causam_500(self):
        response = self.client.post(reverse("admin:reservas_reserva_add"), {"_save": "Salvar"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este campo é obrigatório")

    def test_semente_idempotente_sem_alterar_cadastro_existente(self):
        self.veiculo.ativo = False
        self.veiculo.save()
        for _ in range(2):
            call_command("popular_frota", stdout=StringIO())
        self.assertEqual(Veiculo.objects.count(), 10)
        self.veiculo.refresh_from_db()
        self.assertFalse(self.veiculo.ativo)
