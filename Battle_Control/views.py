from django.shortcuts import render, redirect, get_object_or_404
from .models import Personagem
from .forms import PersonagemForm
import requests

def index_view(request):
    return render(request, 'site/index.html')

def create_view(request):
    if request.method == 'GET':
        form = PersonagemForm()
        return render(request, 'site/criar.html', {'form': form})
    if request.method == 'POST':
        form = PersonagemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rpg:listar')
        
def list_view(request):
    personagens = Personagem.objects.all()
    if personagens:
        return render(request, 'site/listar.html', {'personagens': personagens})
    return render(request, 'site/listar.html')

def detail_view(request, pk):
    personagem = Personagem.objects.get(pk = pk)
    if personagem:
        return render(request, 'site/detalhes.html', {'personagem': personagem})
    
def delete_view(request, pk):
    personagem = Personagem.objects.get(pk = pk)
    if personagem:
        personagem.delete()
        request.status_code = 204
        return redirect('rpg:listar')
    
def update_view(request, pk):
    personagem = Personagem.objects.get(pk = pk)
    if request.method == 'GET':
        form = PersonagemForm(instance=personagem)
        return render(request, 'site/atualizar.html', {'personagem': personagem, 'form': form})
    if request.method == 'POST':
        form = PersonagemForm(request.POST, instance=personagem)
        if form.is_valid():
            form.save()
            return redirect('rpg:listar')
        
def battle_view(request):
    # Inicializa a sessão se ainda não existe
    if 'selecionados' not in request.session:
        request.session['selecionados'] = []

    if request.method == 'POST':
        if 'personagem_id' in request.POST and 'dano' in request.POST:
            personagem_id = int(request.POST.get('personagem_id'))
            dano = int(request.POST.get('dano', 0))
            personagem = get_object_or_404(Personagem, id=personagem_id)
            personagem.receber_dano(dano)
            return redirect('rpg:batalhar')  # Atualiza a tela

        if 'limpar' in request.POST:
            request.session['selecionados'] = []
            request.session.modified = True
            
        if 'remover_id' in request.POST:
            remover_id = int(request.POST.get('remover_id'))
            if remover_id in request.session['selecionados']:
                request.session['selecionados'].remove(remover_id)
                request.session.modified = True
        else:
            id_selecionado = request.POST.get('personagem')
            if id_selecionado and id_selecionado.isdigit():
                id_int = int(id_selecionado)
                if id_int not in request.session['selecionados']:
                    request.session['selecionados'].append(id_int)
                    request.session.modified = True

    # Pega todos os personagens disponíveis
    personagens = Personagem.objects.all()

    # Busca personagens selecionados na sessão
    selecionados_ids = request.session.get('selecionados', [])
    selecionados = Personagem.objects.filter(id__in=selecionados_ids)

    # Agrupa personagens por tipo
    personagens_por_tipo = {}
    for p in selecionados:
        tipo = p.tipo or "Sem tipo"

        if tipo not in personagens_por_tipo:
            personagens_por_tipo[tipo] = []
        personagens_por_tipo[tipo].append(p)

    return render(request, 'site/battle.html', {
        'personagens': personagens,
        'personagens_por_tipo': personagens_por_tipo,
    })