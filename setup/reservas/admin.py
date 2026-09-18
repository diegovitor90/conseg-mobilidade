from django.contrib import admin

from .forms import ReservaForm
from .models import Motorista, Reserva, Veiculo

admin.site.site_header = "COSEG Mobilidade"
admin.site.site_title = "COSEG Admin"
admin.site.index_title = "Gestão de transportes"


@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "categoria", "capacidade", "ativo")
    list_filter = ("categoria", "ativo")
    search_fields = ("codigo",)
    readonly_fields = ("capacidade", "criado_em", "atualizado_em")


@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ("nome", "matricula", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "matricula")
    readonly_fields = ("criado_em", "atualizado_em")


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    form = ReservaForm
    actions = ["delete_selected"]
    list_display = ("solicitante", "data", "horario_saida", "horario_retorno", "quantidade_passageiros", "veiculo", "motorista")
    list_filter = ("data", "veiculo")
    search_fields = ("solicitante", "setor", "destino")
    autocomplete_fields = ("veiculo", "motorista")
    readonly_fields = ("criado_em", "atualizado_em")
    date_hierarchy = "data"
