from django.urls import path
from .views import index_view, list_view, create_view, delete_view, detail_view, update_view, battle_view

app_name = 'rpg'
urlpatterns = [
    path('home/', index_view, name='index'),
    path('criar/', create_view, name='criar'),
    path('listar/', list_view, name='listar'),
    path('detail/<int:pk>', detail_view, name='mostrar'),
    path('atualizar/<int:pk>', update_view, name='atualizar'),
    path('deletar/<int:pk>', delete_view, name='deletar'),
    path('battle/', battle_view, name='batalhar'),
]