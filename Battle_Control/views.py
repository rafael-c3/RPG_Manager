from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from .models import Personagem, Inventario, Item, Efeito, EfeitoAplicado, ItemAplicado
from .forms import PersonagemForm
from django.http import HttpResponse
from collections import defaultdict
from django.views.decorators.http import require_POST

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
        

        
def inicializar_sessao(request):
    if 'selecionados' not in request.session:
        request.session['selecionados'] = []

def aplicar_dano(request):
    personagem_id = request.POST.get("personagem_id")
    personagem = get_object_or_404(Personagem, id=personagem_id)
    dano = int(request.POST.get("dano", 0))
    critico = request.POST.get("critico") == "on"

    modificador_total = sum([e.efeito.modificador_dano for e in personagem.efeitos_aplicados.filter(ativo=True)])

    dano_base = dano
    bonus = modificador_total

    if critico:
        dano_total = (dano_base * 2) + bonus
        personagem.armadura = max(personagem.armadura - 1, 0)
        dano_final = dano_total
    else:
        dano_total = dano_base + bonus
        dano_final = max(dano_total - personagem.resistencia, 0)

    if personagem.barreira_magica > 0:
        if dano_final <= personagem.barreira_magica:
            personagem.barreira_magica -= dano_final
            dano_final = 0
        else:
            dano_final -= personagem.barreira_magica
            personagem.barreira_magica = 0

    personagem.vida = max(personagem.vida - dano_final, 0)
    personagem.save()

def aplicar_cura(request):
    personagem_id = int(request.POST.get('personagem_id'))
    cura = int(request.POST.get('cura', 0))
    personagem = get_object_or_404(Personagem, id=personagem_id)
    personagem.vida += cura
    personagem.save()

def dano_armadura(request):
    personagem_id = int(request.POST.get('personagem_id'))
    dano = int(request.POST.get('armadura_dano', 0))
    personagem = get_object_or_404(Personagem, id=personagem_id)
    personagem.armadura = max(0, personagem.armadura - dano)
    personagem.save()

def aplicar_efeito(request):
    efeito_id = int(request.POST['efeito_id'])
    personagem_id = int(request.POST['personagem_id'])
    personagem = get_object_or_404(Personagem, id=personagem_id)
    efeito = get_object_or_404(Efeito, id=efeito_id)
    efeito_aplicado = EfeitoAplicado.objects.create(personagem=personagem, efeito=efeito)
    efeito_aplicado.aplicar()

def remover_efeito(request):
    efeito_aplicado = get_object_or_404(EfeitoAplicado, id=request.POST['remover_efeito_id'])
    efeito_aplicado.remover()

def usar_item(request):
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
    elif item.atributo_afetado == 'barreira_magica':
        personagem.barreira_magica += item.valor_efeito

    if item.reversivel:
        ItemAplicado.objects.create(personagem=personagem, item=item)

    inventario.quantidade -= 1
    if inventario.quantidade <= 0:
        inventario.delete()
    else:
        inventario.save()
    personagem.save()

def remover_item_aplicado(request):
    aplicado = get_object_or_404(ItemAplicado, id=request.POST.get("remover_item_aplicado_id"))
    personagem = aplicado.personagem
    item = aplicado.item

    valor = Decimal(item.valor_efeito)
    atributo = item.atributo_afetado
    if hasattr(personagem, atributo):
        setattr(personagem, atributo, getattr(personagem, atributo) - valor)
        personagem.save()

    aplicado.ativo = False
    aplicado.save()

def alterar_turno(request, aumentar=True):
    personagem_id = int(request.POST.get('personagem_id'))
    personagem = get_object_or_404(Personagem, id=personagem_id)
    if aumentar:
        personagem.turno += 1
    else:
        personagem.turno = max(0, personagem.turno - 1)
    personagem.save()

def battle_view(request):
    inicializar_sessao(request)

    if request.method == 'POST':
        if 'dano' in request.POST:
            aplicar_dano(request)
        elif 'cura' in request.POST:
            aplicar_cura(request)
            return redirect('rpg:batalhar')
        elif 'armadura_dano' in request.POST:
            dano_armadura(request)
            return redirect('rpg:batalhar')
        elif 'efeito_id' in request.POST:
            aplicar_efeito(request)
            return redirect('rpg:batalhar')
        elif 'remover_efeito_id' in request.POST:
            remover_efeito(request)
            return redirect('rpg:batalhar')
        elif 'usar_item' in request.POST:
            usar_item(request)
            return redirect('rpg:batalhar')
        elif 'remover_item_aplicado_id' in request.POST:
            remover_item_aplicado(request)
        elif 'aumentar_turno' in request.POST:
            alterar_turno(request, aumentar=True)
            return redirect('rpg:batalhar')
        elif 'diminuir_turno' in request.POST:
            alterar_turno(request, aumentar=False)
            return redirect('rpg:batalhar')
        elif 'limpar' in request.POST:
            request.session['selecionados'] = []
            request.session.modified = True
        elif 'remover_id' in request.POST:
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

    personagens = Personagem.objects.all()
    buffs = Efeito.objects.filter(tipo='buff')
    debuffs = Efeito.objects.filter(tipo='debuff')
    habilidades = Efeito.objects.filter(tipo='habilidade')

    selecionados_ids = request.session.get('selecionados', [])
    selecionados = Personagem.objects.filter(id__in=selecionados_ids)

    personagens_por_tipo = {}
    for p in selecionados:
        tipo = p.tipo or "Sem tipo"
        if tipo not in personagens_por_tipo:
            personagens_por_tipo[tipo] = []
        personagens_por_tipo[tipo].append(p)

    return render(request, 'site/battle.html', {
        'personagens': personagens,
        'personagens_por_tipo': personagens_por_tipo,
        'buffs': buffs,
        'debuffs': debuffs,
        'habilidades': habilidades,
    })

def adventure_view(request):
    personagens = Personagem.objects.all()
    itens = Item.objects.all()

    if request.method == "POST":
        personagem_id = request.POST.get("personagem_id")
        item_id = request.POST.get("item_id")
        quantidade = int(request.POST.get("quantidade", 1))

        personagem = get_object_or_404(Personagem, id=personagem_id)
        item = get_object_or_404(Item, id=item_id)

        inventario, criado = Inventario.objects.get_or_create(personagem=personagem, item=item)
        inventario.quantidade += quantidade
        inventario.save()

        return redirect("rpg:adventure")

    # Estrutura: lista de dicionários por personagem
    inventarios_por_personagem = []
    for personagem in personagens:
        inventario_do_personagem = Inventario.objects.filter(personagem=personagem).select_related("item")
        inventarios_por_personagem.append({
            "personagem": personagem,
            "itens": inventario_do_personagem
        })

    return render(request, "site/adventure.html", {
        "personagens": personagens,
        "itens": itens,
        "inventarios_por_personagem": inventarios_por_personagem,
    })

@require_POST
def remover_item(request, inventario_id):
    inventario = get_object_or_404(Inventario, id=inventario_id)
    inventario.delete()
    return redirect("rpg:adventure")

@require_POST
def editar_item(request, inventario_id):
    inventario = get_object_or_404(Inventario, id=inventario_id)
    nova_quantidade = int(request.POST.get("quantidade", 1))
    inventario.quantidade = nova_quantidade
    inventario.save()
    return redirect("rpg:adventure")