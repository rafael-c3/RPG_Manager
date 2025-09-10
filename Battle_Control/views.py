from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from .models import Personagem, Inventario, Item, Efeito, EfeitoAplicado, ItemAplicado, Dinheiro
from .forms import PersonagemForm, InventarioForm, DinheiroForm
from django.http import HttpResponse, JsonResponse
from collections import defaultdict
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string


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
    
        
@require_POST
def aplicar_dano(request):
    """Aplica dano a um personagem."""
    try:
        personagem_id = int(request.POST.get("personagem_id"))
        dano_base = Decimal(request.POST.get("dano", "0"))
        is_critico = request.POST.get("critico") == "on"
    except (ValueError, TypeError):
        return JsonResponse({"erro": "Valores inválidos fornecidos."}, status=400)

    personagem = get_object_or_404(Personagem, id=personagem_id)
    
    # A lógica do modelo já está correta
    dano_sofrido = personagem.receber_dano_calculado(dano_base, is_critico)
    
    # --- CORREÇÃO AQUI ---
    # Agora retornamos os dados no formato que o JavaScript espera
    return JsonResponse({
        "mensagem": f"{personagem.nome} recebeu {dano_sofrido:.1f} de dano!",
        "personagem_id": personagem.id,
        "atributos_atualizados": personagem.get_atributos_dict()
    })


@csrf_exempt 
@require_POST
def aplicar_cura(request):
    """Aplica cura a um personagem."""
    try:
        personagem_id = int(request.POST.get('personagem_id'))
        cura_base = Decimal(request.POST.get('cura', '0'))
        is_critico = request.POST.get('critico') == 'on'
    except (ValueError, TypeError):
        return JsonResponse({"erro": "Valores inválidos fornecidos."}, status=400)

    personagem = get_object_or_404(Personagem, pk=personagem_id)
    
    cura_final = cura_base * Decimal('1.5') if is_critico else cura_base
    
    personagem.curar(cura_final)

    # --- CORREÇÃO AQUI TAMBÉM ---
    # Agora retornamos os dados no formato que o JavaScript espera
    return JsonResponse({
        "mensagem": f"{personagem.nome} foi curado em {cura_final:.1f} pontos!",
        "personagem_id": personagem.id,
        "atributos_atualizados": personagem.get_atributos_dict()
    })

@require_POST
def aplicar_efeito(request):
    """Aplica um efeito (buff/debuff) a um personagem."""
    personagem_id = request.POST.get('personagem_id')
    efeito_id = request.POST.get('efeito_id')

    if not personagem_id or not efeito_id:
        return JsonResponse({"erro": "IDs do personagem e do efeito são obrigatórios."}, status=400)

    personagem = get_object_or_404(Personagem, id=personagem_id)
    efeito = get_object_or_404(Efeito, id=efeito_id)

    # A lógica de criação e aplicação já está corretamente nos modelos.
    efeito_aplicado, criado = EfeitoAplicado.objects.get_or_create(
        personagem=personagem, 
        efeito=efeito,
        defaults={'ativo': True}
    )
    
    if criado:
        efeito_aplicado.aplicar()
        mensagem = f"Efeito '{efeito.nome}' aplicado a {personagem.nome}."
    else:
        # Se o efeito já existe, podemos reativá-lo ou apenas informar.
        if not efeito_aplicado.ativo:
            efeito_aplicado.ativo = True
            efeito_aplicado.aplicar() # Reaplicar se necessário
            mensagem = f"Efeito '{efeito.nome}' reativado em {personagem.nome}."
        else:
            mensagem = f"{personagem.nome} já está sob o efeito '{efeito.nome}'."
    
    # Retorna os atributos atualizados do personagem para o frontend.
    return JsonResponse({
        "mensagem": mensagem,
        "personagem_id": personagem.id,
        "atributos_atualizados": personagem.get_atributos_dict() # Método a ser criado no modelo.
    })

@require_POST
def remover_efeito(request):
    """Remove um efeito aplicado de um personagem."""
    efeito_aplicado_id = request.POST.get('remover_efeito_id')
    efeito_aplicado = get_object_or_404(EfeitoAplicado, id=efeito_aplicado_id)
    
    personagem = efeito_aplicado.personagem
    efeito_nome = efeito_aplicado.efeito.nome

    efeito_aplicado.remover() # A lógica já está no modelo, ótimo!

    return JsonResponse({
        "mensagem": f"Efeito '{efeito_nome}' removido de {personagem.nome}.",
        "personagem_id": personagem.id,
        "atributos_atualizados": personagem.get_atributos_dict() # Retorna dados atualizados
    })

@require_POST
def usar_item(request):
    """Faz um personagem usar um item do inventário."""
    try:
        personagem_id = int(request.POST.get('personagem_id'))
        item_id = int(request.POST.get('item_id'))
    except (ValueError, TypeError):
        return JsonResponse({"erro": "IDs inválidos."}, status=400)
        
    personagem = get_object_or_404(Personagem, id=personagem_id)
    
    # A lógica de uso do item foi movida para o modelo Personagem.
    # (Você precisará adicionar este método ao seu models.py)
    try:
        mensagem_resultado = personagem.usar_item_do_inventario(item_id)
    except Inventario.DoesNotExist:
        return JsonResponse({"erro": "Item não encontrado no inventário."}, status=404)
    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=400)

    return JsonResponse({
        "mensagem": mensagem_resultado,
        "personagem_id": personagem.id,
        "atributos_atualizados": personagem.get_atributos_dict()
    })

# --- View Principal da Batalha ---

def battle_view(request):
    """
    Renderiza a página de batalha e lida com a seleção de personagens na sessão.
    As ações de combate (dano, cura, etc.) devem ser feitas por chamadas AJAX
    para as views de ação específicas acima.
    """
    # Inicializa a lista de selecionados na sessão se não existir.
    request.session.setdefault('selecionados', [])

    if request.method == 'POST':
        # Esta view agora só lida com a manipulação da lista de personagens
        personagem_id_str = request.POST.get('personagem')
        remover_id_str = request.POST.get('remover_id')

        if 'limpar' in request.POST:
            request.session['selecionados'] = []
        elif remover_id_str and remover_id_str.isdigit():
            remover_id = int(remover_id_str)
            if remover_id in request.session['selecionados']:
                request.session['selecionados'].remove(remover_id)
        elif personagem_id_str and personagem_id_str.isdigit():
            personagem_id = int(personagem_id_str)
            if personagem_id not in request.session['selecionados']:
                request.session['selecionados'].append(personagem_id)
        
        request.session.modified = True
        return redirect('rpg:batalhar') # Redireciona para atualizar a lista na tela

    # Lógica para GET (carregamento inicial da página)
    personagens = Personagem.objects.all().order_by('nome')
    efeitos = Efeito.objects.all()
    
    selecionados_ids = request.session.get('selecionados', [])
    selecionados = Personagem.objects.filter(id__in=selecionados_ids)

    # Agrupa os personagens por tipo para exibição
    personagens_por_tipo = {}
    for p in selecionados:
        tipo = p.get_tipo_display() # Usa o método do Django para obter o nome legível
        personagens_por_tipo.setdefault(tipo, []).append(p)

    context = {
        'personagens': personagens,
        'personagens_por_tipo': personagens_por_tipo,
        'buffs': efeitos.filter(tipo='buff'),
        'debuffs': efeitos.filter(tipo='debuff'),
        'habilidades': efeitos.filter(tipo='habilidade'),
    }
    return render(request, 'site/battle.html', context)


def inventario_lista(request):
    personagens = Personagem.objects.prefetch_related('inventario_set__item')

    # Form para adicionar direto de cada card
    novo_form = InventarioForm()
    return render(request, 'site/inventario_lista.html', {
        'personagens': personagens,
        'novo_form': novo_form,
    })

def inventario_update(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'decrement':
            if inv.quantidade > 1:
                inv.quantidade -= 1
                inv.save()
            else:
                inv.delete()  # Remove o item quando quantidade chega a 0
        elif action == 'increment':
            inv.quantidade += 1
            inv.save()
    return redirect('rpg:inventario_lista')

def inventario_add(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            obj, created = Inventario.objects.get_or_create(
                personagem=form.cleaned_data['personagem'],
                item=form.cleaned_data['item'],
                defaults={'quantidade': form.cleaned_data['quantidade']}
            )
            if not created:
                obj.quantidade += form.cleaned_data['quantidade']
                obj.save()
    return redirect('rpg:inventario_lista')

def dinheiro_update(request):
    if request.method == 'POST':
        form = DinheiroForm(request.POST)
        if form.is_valid():
            moeda = form.cleaned_data['moeda']
            valor = form.cleaned_data['valor']
            acao = form.cleaned_data['acao']

            # Considera o primeiro personagem como dono da carteira global
            dono = Personagem.objects.first()
            dinheiro = dono.dinheiro

            if acao == 'add':
                setattr(dinheiro, moeda, getattr(dinheiro, moeda) + valor)
            elif acao == 'sub':
                atual = getattr(dinheiro, moeda)
                novo = max(0, atual - valor)
                setattr(dinheiro, moeda, novo)

            dinheiro.converter_para_superiores()

    return redirect('rpg:inventario_lista')