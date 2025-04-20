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
        
def battle_view(request):
    # Inicializa a sessão se ainda não existe
    if 'selecionados' not in request.session:
        request.session['selecionados'] = []

    if request.method == 'POST':
        if 'personagem_id' in request.POST and 'dano' in request.POST:
            personagem_id = request.POST.get("personagem_id")
            personagem = Personagem.objects.get(id=personagem_id)
            dano = int(request.POST.get("dano", 0))
            critico = request.POST.get("critico") == "on"

            # Modificador de dano de efeitos ativos
            modificador_total = 0
            for efeito in personagem.efeitos_aplicados.filter(ativo=True):
                modificador_total += efeito.efeito.modificador_dano

            dano_base = dano
            bonus = modificador_total

            if critico:
                dano_total = (dano_base * 2) + bonus  # dobra só o base e soma o bônus
                personagem.armadura = max(personagem.armadura - 1, 0)  # -1 armadura
                dano_final = dano_total  # ignora resistência
            else:
                dano_total = dano_base + bonus
                dano_final = max(dano_total - personagem.resistencia, 0)

            # Aplicar dano à barreira mágica primeiro, depois à vida
            if personagem.barreira_magica > 0:
                if dano_final <= personagem.barreira_magica:
                    personagem.barreira_magica -= dano_final
                    dano_final = 0
                else:
                    dano_final -= personagem.barreira_magica
                    personagem.barreira_magica = 0

            # Aplicar o restante do dano à vida
            personagem.vida = max(personagem.vida - dano_final, 0)
            personagem.save()
                
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
        
        if 'efeito_id' in request.POST and 'personagem_id' in request.POST:
            efeito_id = int(request.POST['efeito_id'])
            personagem_id = int(request.POST['personagem_id'])
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
        elif item.atributo_afetado == 'barreira_magica':
            personagem.barreira_magica += item.valor_efeito
        # pode fazer mais efeitos depois...
        if item.reversivel:
            ItemAplicado.objects.create(personagem=personagem, item=item)

        inventario.quantidade -= 1
        if inventario.quantidade <= 0:
            inventario.delete()
        else:
            inventario.save()
        personagem.save()

        return redirect('rpg:batalhar')
    
    remover_item_id = request.POST.get("remover_item_aplicado_id")
    if remover_item_id:
        aplicado = ItemAplicado.objects.get(id=remover_item_id)
        personagem = aplicado.personagem
        item = aplicado.item

        # Reverte o efeito (ex: remove o bônus)
        valor = Decimal(item.valor_efeito)
        atributo = item.atributo_afetado
        if hasattr(personagem, atributo):
            setattr(personagem, atributo, getattr(personagem, atributo) - valor)
            personagem.save()

        aplicado.ativo = False
        aplicado.save()

    if 'aumentar_turno' in request.POST:
        personagem_id = int(request.POST.get('personagem_id'))
        personagem = get_object_or_404(Personagem, id=personagem_id)
        personagem.turno += 1
        personagem.save()
        return redirect('rpg:batalhar')

    if 'diminuir_turno' in request.POST:
        personagem_id = int(request.POST.get('personagem_id'))
        personagem = get_object_or_404(Personagem, id=personagem_id)
        personagem.turno = max(0, personagem.turno - 1)  # Evita número negativo
        personagem.save()
        return redirect('rpg:batalhar')

    # Pega todos os personagens disponíveis
    personagens = Personagem.objects.all()
    # Busca os efeitos reversíveis disponíveis
    buffs = Efeito.objects.filter(tipo='buff')
    debuffs = Efeito.objects.filter(tipo='debuff')
    habilidades = Efeito.objects.filter(tipo='habilidade')

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

