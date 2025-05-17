from django.urls import path
from .views import index_view, list_view, create_view, delete_view, detail_view, update_view, battle_view, aplicar_dano, aplicar_cura, aplicar_efeito, inventario_add, inventario_lista, inventario_update, dinheiro_update

app_name = 'rpg'
urlpatterns = [
    path('home/', index_view, name='index'),
    path('criar/', create_view, name='criar'),
    path('listar/', list_view, name='listar'),
    path('detail/<int:pk>', detail_view, name='mostrar'),
    path('atualizar/<int:pk>', update_view, name='atualizar'),
    path('deletar/<int:pk>', delete_view, name='deletar'),
    path('battle/', battle_view, name='batalhar'),
    path('aplicar-dano/', aplicar_dano, name='aplicar_dano'),  # <- Aqui
    path('aplicar-cura/', aplicar_cura, name='aplicar_cura'),
    path("aplicar-efeito/", aplicar_efeito, name="aplicar_efeito"),
    path('inventario/', inventario_lista, name='inventario_lista'),
    path('inventario/add/', inventario_add, name='inventario_add'),
    path('inventario/<int:pk>/update/', inventario_update, name='inventario_update'),
    path('dinheiro/update/', dinheiro_update, name='dinheiro_update'),
]

