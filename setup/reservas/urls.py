from django.urls import path

from . import views

app_name = "reservas"

urlpatterns = [
    path("veiculos/", views.veiculo_lista, name="veiculo_lista"),
    path("veiculos/novo/", views.veiculo_cadastrar, name="veiculo_cadastrar"),
    path("veiculos/<int:pk>/", views.veiculo_detalhe, name="veiculo_detalhe"),
    path("veiculos/<int:pk>/editar/", views.veiculo_editar, name="veiculo_editar"),
    path("veiculos/<int:pk>/desativar/", views.veiculo_desativar, name="veiculo_desativar"),
    path("veiculos/<int:pk>/excluir/", views.veiculo_excluir, name="veiculo_excluir"),
]
