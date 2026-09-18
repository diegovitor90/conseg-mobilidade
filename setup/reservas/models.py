"""Entidades do PBL 1. As regras ficam no servidor, inclusive ao usar o Admin."""
from datetime import date, time

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class RegistroValidado(models.Model):
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # save() sozinho não chama full_clean() no Django.
        self.full_clean()
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"atualizado_em"}
        return super().save(*args, **kwargs)


class Veiculo(RegistroValidado):
    class Categoria(models.TextChoices):
        LEVE = "LEVE", "Veículo leve"
        COLETIVO = "COLETIVO", "Veículo coletivo"

    CAPACIDADES = {Categoria.LEVE: 4, Categoria.COLETIVO: 18}

    codigo = models.CharField("Código do veículo", max_length=10, unique=True)
    categoria = models.CharField("Categoria", max_length=10, choices=Categoria.choices)
    capacidade = models.PositiveSmallIntegerField("Capacidade", editable=False)
    ativo = models.BooleanField("Ativo para novas reservas", default=True)

    class Meta:
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"
        ordering = ["codigo"]
        constraints = [models.CheckConstraint(
            condition=Q(categoria="LEVE", capacidade=4) | Q(categoria="COLETIVO", capacidade=18),
            name="veiculo_categoria_capacidade_coerentes",
        )]

    def clean_fields(self, exclude=None):
        self.codigo = (self.codigo or "").strip().upper()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        self.capacidade = self.CAPACIDADES.get(self.categoria)
        if self._state.adding:
            return
        anterior = type(self).objects.filter(pk=self.pk).first()
        if not anterior:
            return
        erros = {}
        if anterior.categoria != self.categoria and self.reservas.exists():
            erros["categoria"] = "Este veículo possui reservas. Preserve sua categoria e cadastre outro veículo se necessário."
        if anterior.ativo and not self.ativo and Reserva.pendentes().filter(veiculo_id=self.pk).exists():
            erros["ativo"] = "Há reservas em andamento ou futuras. Realoque ou remova essas reservas antes de desativar."
        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        if kwargs.get("update_fields") is not None:
            # Mantém categoria e capacidade sincronizadas em saves parciais.
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"codigo", "categoria", "capacidade"}
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.get_categoria_display()}"


class Motorista(RegistroValidado):
    nome = models.CharField("Nome", max_length=150)
    matricula = models.CharField("Matrícula", max_length=20, unique=True)
    cnh = models.CharField("CNH", max_length=20, unique=True)
    ativo = models.BooleanField("Ativo para novas reservas", default=True)

    class Meta:
        verbose_name = "Motorista"
        verbose_name_plural = "Motoristas"
        ordering = ["nome", "pk"]

    def clean(self):
        super().clean()
        if not self._state.adding and not self.ativo:
            era_ativo = type(self).objects.filter(pk=self.pk, ativo=True).exists()
            if era_ativo and Reserva.pendentes().filter(motorista_id=self.pk).exists():
                raise ValidationError({"ativo": "Há reservas em andamento ou futuras para este motorista."})

    def __str__(self):
        return f"{self.nome} - {self.matricula}"


class Reserva(RegistroValidado):
    solicitante = models.CharField("Solicitante", max_length=150)
    setor = models.CharField("Setor", max_length=100)
    atividade = models.CharField("Atividade", max_length=200)
    origem = models.CharField("Origem", max_length=150)
    destino = models.CharField("Destino", max_length=150)
    data = models.DateField("Data da reserva")
    horario_saida = models.TimeField("Horário de saída")
    horario_retorno = models.TimeField("Horário de retorno")
    quantidade_passageiros = models.PositiveSmallIntegerField(
        "Quantidade de passageiros",
        validators=[MinValueValidator(1), MaxValueValidator(18)],
    )
    categoria_pretendida = models.CharField(
        "Categoria pretendida", max_length=10, choices=Veiculo.Categoria.choices, blank=True,
    )
    veiculo = models.ForeignKey(
        Veiculo, verbose_name="Veículo", on_delete=models.PROTECT,
        related_name="reservas", null=True, blank=True,
    )
    motorista = models.ForeignKey(
        Motorista, verbose_name="Motorista", on_delete=models.PROTECT,
        related_name="reservas", null=True, blank=True,
    )
    observacoes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ["data", "horario_saida", "pk"]
        constraints = [
            models.CheckConstraint(condition=Q(quantidade_passageiros__gte=1, quantidade_passageiros__lte=18), name="reserva_passageiros_1_a_18"),
            models.CheckConstraint(condition=Q(horario_retorno__gt=F("horario_saida")), name="reserva_retorno_apos_saida"),
        ]

    @classmethod
    def pendentes(cls):
        agora = timezone.localtime()
        return cls.objects.filter(
            Q(data__gt=agora.date())
            | Q(data=agora.date(), horario_retorno__gt=agora.time().replace(tzinfo=None))
        )

    def clean(self):
        super().clean()
        erros = {}
        data_valida = isinstance(self.data, date)
        horarios_validos = isinstance(self.horario_saida, time) and isinstance(self.horario_retorno, time)
        passageiros_validos = isinstance(self.quantidade_passageiros, int)
        historica = data_valida and self.data < timezone.localdate()

        if historica:
            anterior = type(self).objects.filter(pk=self.pk).first() if self.pk else None
            campos = ("data", "horario_saida", "horario_retorno", "veiculo_id", "motorista_id", "quantidade_passageiros", "categoria_pretendida")
            if anterior is None or any(getattr(anterior, c) != getattr(self, c) for c in campos):
                erros["data"] = "Não é permitido agendar no passado. Reservas históricas só permitem corrigir dados descritivos."

        if horarios_validos and self.horario_retorno <= self.horario_saida:
            erros["horario_retorno"] = "O retorno deve ser posterior à saída, no mesmo dia."

        # Uma FK inválida deve virar erro de formulário, não uma exceção 500.
        veiculo = Veiculo.objects.filter(pk=self.veiculo_id).first() if self.veiculo_id else None
        motorista = Motorista.objects.filter(pk=self.motorista_id).first() if self.motorista_id else None
        if veiculo:
            if not historica and not veiculo.ativo:
                erros["veiculo"] = "O veículo está inativo."
            if passageiros_validos and self.quantidade_passageiros > veiculo.capacidade:
                erros["quantidade_passageiros"] = f"O veículo {veiculo.codigo} transporta no máximo {veiculo.capacidade} passageiros."
        if motorista and not historica and not motorista.ativo:
            erros["motorista"] = "O motorista está inativo."

        if data_valida and horarios_validos and self.horario_retorno > self.horario_saida:
            conflitos = type(self).objects.filter(
                data=self.data,
                horario_saida__lt=self.horario_retorno,
                horario_retorno__gt=self.horario_saida,
            ).exclude(pk=self.pk)
            if veiculo and conflitos.filter(veiculo_id=veiculo.pk).exists():
                erros["veiculo"] = "Este veículo já possui uma reserva nesse intervalo."
            if motorista and conflitos.filter(motorista_id=motorista.pk).exists():
                erros["motorista"] = "Este motorista já possui uma reserva nesse intervalo."
        if erros:
            raise ValidationError(erros)

    def __str__(self):
        return f"{self.solicitante} - {self.data}"
