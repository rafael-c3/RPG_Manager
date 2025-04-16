from django.shortcuts import render, redirect, get_object_or_404
from .models import Personagem, Inventario, Item, Efeito, EfeitoAplicado
from .forms import PersonagemForm
from django.http import HttpResponse

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
        
        if 'personagem_id' in request.POST and 'cura' in request.POST:
            personagem_id = int(request.POST.get('personagem_id'))
            cura = int(request.POST.get('cura', 0))
            personagem = get_object_or_404(Personagem, id=personagem_id)
            personagem.vida += cura
            personagem.save()
            return redirect('rpg:batalhar')
        
        if 'personagem_id' in request.POST and 'armadura_dano' in request.POST:
            personagem_id = int(request.POST.get('personagem_id'))
            dano_armadura = int(request.POST.get('armadura_dano', 0))
            personagem = get_object_or_404(Personagem, id=personagem_id)
            personagem.armadura = max(0, personagem.armadura - dano_armadura)
            personagem.save()
            return redirect('rpg:batalhar')
        
        if 'personagem_id' in request.POST and 'efeito_id' in request.POST:
            personagem_id = int(request.POST['personagem_id'])
            efeito_id = int(request.POST['efeito_id'])
            personagem = get_object_or_404(Personagem, id=personagem_id)
            efeito = get_object_or_404(Efeito, id=efeito_id)

            efeito_aplicado = EfeitoAplicado.objects.create(personagem=personagem, efeito=efeito)
            efeito_aplicado.aplicar()
            return redirect('rpg:batalhar')

        elif 'remover_efeito_id' in request.POST:
            efeito_aplicado = get_object_or_404(EfeitoAplicado, id=request.POST['remover_efeito_id'])
            efeito_aplicado.remover()
            return redirect('rpg:batalhar')

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

    if 'usar_item' in request.POST:
        personagem_id = int(request.POST.get('personagem_id'))
        item_id = int(request.POST.get('item_id'))
        personagem = get_object_or_404(Personagem, id=personagem_id)
        inventario = get_object_or_404(Inventario, personagem=personagem, item_id=item_id)

        item = inventario.item
        if item.atributo_afetado == 'vida':
            personagem.curar(item.valor_efeito)
        elif item.atributo_afetado == 'mana':
            personagem.mana += item.valor_efeito
        elif item.atributo_afetado == 'armadura':
            personagem.armadura += item.valor_efeito
        # pode fazer mais efeitos depois...

        inventario.quantidade -= 1
        if inventario.quantidade <= 0:
            inventario.delete()
        else:
            inventario.save()
        personagem.save()

        return redirect('rpg:batalhar')

    # Pega todos os personagens disponíveis
    personagens = Personagem.objects.all()
    # Busca os efeitos reversíveis disponíveis
    efeitos = Efeito.objects.all()  # mostra todos
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
        'efeitos': efeitos,

    })