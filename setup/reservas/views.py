"""CRUD de veículos adaptado do padrão da Oficina Web, dentro de reservas."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import EntrarForm, VeiculoForm
from .models import Veiculo


class CustomLoginView(LoginView):
    form_class = EntrarForm
    template_name = "reservas/entrar.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            return next_url
        return super().get_success_url()


@login_required
@permission_required("reservas.view_veiculo", raise_exception=True)
@require_GET
def veiculo_lista(request):
    termo = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "")
    situacao = request.GET.get("situacao", "")
    veiculos = Veiculo.objects.all()
    if termo:
        veiculos = veiculos.filter(codigo__icontains=termo)
    if categoria in Veiculo.Categoria.values:
        veiculos = veiculos.filter(categoria=categoria)
    if situacao in ("ativo", "inativo"):
        veiculos = veiculos.filter(ativo=situacao == "ativo")
    pagina = Paginator(veiculos, 8).get_page(request.GET.get("page"))
    filtros = request.GET.copy()
    filtros.pop("page", None)
    totais = Veiculo.objects.aggregate(total=Count("pk"), ativos=Count("pk", filter=Q(ativo=True)), inativos=Count("pk", filter=Q(ativo=False)))
    return render(request, "reservas/veiculos/lista.html", {
        "pagina": pagina, "termo": termo, "categoria": categoria, "situacao": situacao,
        "categorias": Veiculo.Categoria.choices, "filtros": filtros.urlencode(), "totais": totais,
    })


def _formulario(request, veiculo=None):
    form = VeiculoForm(request.POST if request.method == "POST" else None, instance=veiculo)
    if request.method == "POST" and form.is_valid():
        try:
            # A constraint UNIQUE também protege envios simultâneos do mesmo código.
            with transaction.atomic():
                registro = form.save()
        except ValidationError as erro:
            form.add_error(None, erro.messages)
        except IntegrityError:
            form.add_error(None, "Não foi possível salvar. Verifique se o código já foi cadastrado e tente novamente.")
        else:
            messages.success(request, "Veículo atualizado com sucesso." if veiculo else "Veículo cadastrado com sucesso.")
            return redirect("reservas:veiculo_detalhe", pk=registro.pk)
    return render(request, "reservas/veiculos/form.html", {
        "form": form, "veiculo": veiculo, "capacidades": Veiculo.CAPACIDADES,
    })


@login_required
@permission_required(("reservas.view_veiculo", "reservas.add_veiculo"), raise_exception=True)
@require_http_methods(["GET", "POST"])
def veiculo_cadastrar(request):
    return _formulario(request)


@login_required
@permission_required(("reservas.view_veiculo", "reservas.change_veiculo"), raise_exception=True)
@require_http_methods(["GET", "POST"])
def veiculo_editar(request, pk):
    return _formulario(request, get_object_or_404(Veiculo, pk=pk))


@login_required
@permission_required("reservas.view_veiculo", raise_exception=True)
@require_GET
def veiculo_detalhe(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    return render(request, "reservas/veiculos/detalhe.html", {"veiculo": veiculo, "total_reservas": veiculo.reservas.count()})


@login_required
@permission_required(("reservas.view_veiculo", "reservas.change_veiculo"), raise_exception=True)
@require_http_methods(["GET", "POST"])
def veiculo_desativar(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    if request.method == "POST":
        if request.POST.get("confirmar") != "sim":
            messages.error(request, "Marque a confirmação para desativar o veículo.")
        else:
            veiculo.ativo = False
            try:
                veiculo.save(update_fields=["ativo"])
            except ValidationError as erro:
                veiculo.refresh_from_db()
                messages.error(request, " ".join(erro.messages))
            else:
                messages.success(request, "Veículo desativado. O histórico foi preservado.")
                return redirect("reservas:veiculo_detalhe", pk=pk)
    return render(request, "reservas/veiculos/confirmar.html", {"veiculo": veiculo, "acao": "desativar"})


@login_required
@permission_required(("reservas.view_veiculo", "reservas.delete_veiculo"), raise_exception=True)
@require_http_methods(["GET", "POST"])
def veiculo_excluir(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    if request.method == "POST":
        if request.POST.get("confirmar") != "sim":
            messages.error(request, "Marque a confirmação para excluir o veículo.")
        else:
            try:
                with transaction.atomic():
                    veiculo.delete()
            except ProtectedError:
                messages.error(request, "Este veículo possui reservas e não pode ser excluído. Seu histórico precisa ser preservado.")
            else:
                messages.success(request, "Veículo excluído com sucesso.")
                return redirect("reservas:veiculo_lista")
    return render(request, "reservas/veiculos/confirmar.html", {
        "veiculo": veiculo, "acao": "excluir", "protegido": veiculo.reservas.exists(),
    })
