from django.contrib import admin
from .models import Personagem, Item, Inventario, Efeito, EfeitoModificador, EfeitoAplicado

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'atributo_afetado', 'valor_efeito')
    list_filter = ('tipo',)
    search_fields = ('nome', 'descricao')

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('personagem', 'item', 'quantidade')
    list_filter = ('personagem', 'item')

@admin.register(Personagem)
class PersonagemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'vida', 'defesa', 'armadura', 'força')
    search_fields = ('nome',)

class EfeitoModificadorInline(admin.TabularInline):
    model = EfeitoModificador
    extra = 1

class EfeitoAdmin(admin.ModelAdmin):
    inlines = [EfeitoModificadorInline]
    list_display = ('nome', 'tipo', 'reversivel', 'modificador_dano')
    list_filter = ('tipo', 'reversivel')
    search_fields = ('nome',)

admin.site.register(Efeito, EfeitoAdmin)
admin.site.register(EfeitoAplicado)
