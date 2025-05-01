from django.urls import path
from .views import index_view, list_view, create_view, delete_view, detail_view, update_view, battle_view, adventure_view, aplicar_dano, aplicar_cura, aplicar_efeito, remover_item, editar_item, editar_dinheiro

app_name = 'rpg'
urlpatterns = [
    path('home/', index_view, name='index'),
    path('criar/', create_view, name='criar'),
    path('listar/', list_view, name='listar'),
    path('detail/<int:pk>', detail_view, name='mostrar'),
    path('atualizar/<int:pk>', update_view, name='atualizar'),
    path('deletar/<int:pk>', delete_view, name='deletar'),
    path('battle/', battle_view, name='batalhar'),
    path("adventure/", adventure_view, name="adventure"),
    path('aplicar-dano/', aplicar_dano, name='aplicar_dano'),  # <- Aqui
    path('aplicar-cura/', aplicar_cura, name='aplicar_cura'),
    path("aplicar-efeito/", aplicar_efeito, name="aplicar_efeito"),
    path("remover-item/<int:inventario_id>/", remover_item, name="remover_item"),
    path("editar-item/<int:inventario_id>/", editar_item, name="editar_item"),
    path("editar-dinheiro/<int:personagem_id>/", editar_dinheiro, name="editar_dinheiro"),

]

