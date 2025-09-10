from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Personagem(models.Model):
    Tipo_Personagem = [
        ('Aliado', 'Aliado'),
        ('Inimigo', 'Inimigo'),
    ]

    nome = models.CharField(max_length=20)
    tipo = models.CharField(max_length=10, choices=Tipo_Personagem, default='Aliado')
    level = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(999)], default=0)

    vida = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    vida_maxima = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    defesa = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    armadura = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    força = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    magia = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    mana = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    agilidade = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    resistencia = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    necro = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    sorte = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    barreira_magica = models.PositiveIntegerField(default=0)
    turno = models.IntegerField(default=0)

    imagem = models.ImageField(upload_to='imagens/', null=True, blank=True)

    # Lógica da Armadura e Defesa
    @property
    def defesa_total(self):
        return self.defesa + self.armadura
    def reduzir_armadura(self, valor):
        self.armadura = max(self.armadura - valor, 0)
        self.save()
    def reduzir_defesa_total(self, valor):
        # Reduz apenas a defesa_base, sem afetar a armadura
        nova_defesa = self.defesa_total - valor
        nova_defesa_base = max(nova_defesa - self.armadura, 0)
        self.defesa = nova_defesa_base
        self.save()

    # Lógica da Vida e Resistencia
    def receber_dano(self, dano):
        dano_reduzido = max(dano - self.resistencia, 0)
        self.vida = max(self.vida - dano_reduzido, 0)
        self.save()

    def curar(self, quantidade):
        if not isinstance(quantidade, Decimal):
            quantidade = Decimal(quantidade)
        self.vida += quantidade
        if self.vida_maxima:
            self.vida = min(self.vida, self.vida_maxima)
        self.save()

    def receber_dano_calculado(self, dano_base, is_critico=False):
        """
        Calcula e aplica dano, considerando efeitos, crítico, resistência e barreiras.
        Retorna o valor final do dano que foi de fato subtraído da vida.
        """
        # Passo 1: Calcular o dano base + bônus/punições de efeitos
        modificador_total = sum(e.efeito.modificador_dano for e in self.efeitos_aplicados.filter(ativo=True))
        
        # Passo 2: Aplicar o multiplicador de crítico, se houver
        if is_critico:
            # Crítico dobra o dano base e DEPOIS soma os modificadores
            dano_total = (dano_base * 2) + modificador_total 
            
            # REGRA: Armadura é reduzida em 1 ao receber um crítico
            self.reduzir_armadura(1)
        else:
            dano_total = dano_base + modificador_total

        # Passo 3: Subtrair a Resistência (CORREÇÃO PRINCIPAL)
        # REGRA: Resistência anula uma parte do dano (redução fixa)
        dano_apos_resistencia = max(dano_total - self.resistencia, 0)

        # Passo 4: Dano é absorvido pela Barreira Mágica, se houver
        dano_final_antes_barreira = dano_apos_resistencia
        dano_absorvido_barreira = 0
        if self.barreira_magica > 0:
            if dano_final_antes_barreira <= self.barreira_magica:
                self.barreira_magica -= dano_final_antes_barreira
                dano_absorvido_barreira = dano_final_antes_barreira
            else:
                dano_absorvido_barreira = self.barreira_magica
                self.barreira_magica = 0
        
        dano_final_na_vida = dano_final_antes_barreira - dano_absorvido_barreira

        # Passo 5: Aplicar o dano final à vida
        vida_antiga = self.vida
        self.vida = max(self.vida - dano_final_na_vida, 0)
        self.save() # Salva todas as alterações (vida, armadura, barreira)
        
        # Retorna o dano total que o personagem de fato perdeu de vida
        return vida_antiga - self.vida

    def usar_item_do_inventario(self, item_id):
        """
        Busca um item no inventário, aplica seu efeito e o consome.
        """
        inventario_item = Inventario.objects.get(personagem=self, item_id=item_id)
        item = inventario_item.item

        atributo = item.atributo_afetado
        valor = item.valor_efeito

        if not hasattr(self, atributo):
            raise ValueError(f"Atributo '{atributo}' desconhecido.")

        if atributo == 'vida':
            self.curar(valor)
        else:
            valor_atual = getattr(self, atributo)
            setattr(self, atributo, valor_atual + valor)

        if item.reversivel:
            ItemAplicado.objects.create(personagem=self, item=item)
        
        # Consumir item
        inventario_item.quantidade -= 1
        if inventario_item.quantidade <= 0:
            inventario_item.delete()
        else:
            inventario_item.save()
        
        self.save()
        return f"{self.nome} usou {item.nome}."

    def get_atributos_dict(self):
        """Retorna um dicionário com os atributos atuais do personagem, útil para respostas JSON."""
        return {
            "vida": float(self.vida),
            "vida_maxima": float(self.vida_maxima),
            "defesa": float(self.defesa),
            "armadura": float(self.armadura),
            "defesa_total": float(self.defesa_total),
            "forca": float(self.força),
            "magia": float(self.magia),
            "mana": float(self.mana),
            "agilidade": float(self.agilidade),
            "resistencia": float(self.resistencia),
            "necro": float(self.necro),
            "sorte": float(self.sorte),
            "barreira_magica": float(self.barreira_magica),
            "turno": self.turno
        }

    def __str__(self):
        return self.nome
    
class Item(models.Model):
    TIPO_ITEM = [
        ('poção', 'Poção'),
    ]
    nome = models.CharField(max_length=50)
    tipo = models.CharField(max_length=10, choices=TIPO_ITEM, default='Poção')
    descricao = models.TextField(blank=True)
    valor_efeito = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    reversivel = models.BooleanField(default=False)
    atributo_afetado = models.CharField(max_length=20, choices=[
        ('vida', 'Vida'),
        ('defesa', 'Defesa'),
        ('armadura', 'Armadura'),
        ('força', 'Força'),
        ('magia', 'Magia'),
        ('mana', 'Mana'),
        ('agilidade', 'Agilidade'),
        ('resistencia', 'Resistência'),
        ('necro', 'Necro'),
        ('sorte', 'Sorte'),
        ('barreira_magica', 'Barreira Mágica')
    ])

    def __str__(self):
        return self.nome
    
class ItemAplicado(models.Model):
    personagem = models.ForeignKey(Personagem, on_delete=models.CASCADE, related_name='itens_aplicados')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    ativo = models.BooleanField(default=True)
    data_aplicacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.nome} em {self.personagem.nome}"

class Inventario(models.Model):
    personagem = models.ForeignKey(Personagem, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.personagem.nome} - {self.item.nome} x{self.quantidade}"
    
class Efeito(models.Model):
    TIPOS = [
        ('buff', 'Buff'),
        ('debuff', 'Debuff'),
        ('habilidade', 'Habilidade'),
        ('arma', 'Arma'),
    ]

    nome = models.CharField(max_length=50)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    reversivel = models.BooleanField(default=True, help_text="Se marcado, o efeito será revertido ao ser removido.")
    modificador_dano = models.IntegerField(default=0)  # positivo ou negativo

    def __str__(self):
        return f"{self.nome} ({self.tipo})"


class EfeitoModificador(models.Model):
    ATRIBUTOS = (
        ('vida', 'Vida'),
        ('defesa', 'Defesa'),
        ('armadura', 'Armadura'),
        ('força', 'Força'),
        ('magia', 'Magia'),
        ('mana', 'Mana'),
        ('agilidade', 'Agilidade'),
        ('resistencia', 'Resistência'),
        ('necro', 'Necro'),
        ('sorte', 'Sorte'),
        ('barreira_magica', 'Barreira Mágica')
    )

    efeito = models.ForeignKey(Efeito, on_delete=models.CASCADE, related_name='modificadores')
    atributo = models.CharField(max_length=20, choices=ATRIBUTOS)
    valor = models.DecimalField(max_digits=5, decimal_places=1)

    def __str__(self):
        return f"{self.atributo} {self.valor:+}"


class EfeitoAplicado(models.Model):
    personagem = models.ForeignKey(Personagem, on_delete=models.CASCADE, related_name='efeitos_aplicados')
    efeito = models.ForeignKey(Efeito, on_delete=models.CASCADE)
    ativo = models.BooleanField(default=True)

    # Armazenar modificações aplicadas, para reversão
    modificacoes_aplicadas = models.JSONField(default=dict)

    def aplicar(self):
        self.modificacoes_aplicadas = {}

        for modificador in self.efeito.modificadores.all():
            atributo = modificador.atributo
            valor = modificador.valor

            if atributo == 'vida':
                # Cura deve respeitar vida_maxima
                self.personagem.curar(valor)
            else:
                original = getattr(self.personagem, atributo)
                setattr(self.personagem, atributo, original + valor)
                self.modificacoes_aplicadas[atributo] = float(valor)

        self.personagem.save()
        self.save()

    def remover(self):
        if self.efeito.reversivel:
            for mod in self.efeito.modificadores.all():
                atributo = mod.atributo
                valor = Decimal(mod.valor)
                atual = getattr(self.personagem, atributo)
                setattr(self.personagem, atributo, atual - valor)
            self.personagem.save()
        self.ativo = False
        self.save()

    def __str__(self):
        return f"{self.efeito.nome} em {self.personagem.nome}"
    
class Dinheiro(models.Model):
    personagem = models.OneToOneField(Personagem, on_delete=models.CASCADE, related_name="dinheiro")
    cobre = models.PositiveIntegerField(default=0)
    prata = models.PositiveIntegerField(default=0)
    ouro = models.PositiveIntegerField(default=0)
    platina = models.PositiveIntegerField(default=0)

    def converter_para_superiores(self):
        # Cobre para prata
        self.prata += self.cobre // 100
        self.cobre = self.cobre % 100

        # Prata para ouro
        self.ouro += self.prata // 100
        self.prata = self.prata % 100

        # Ouro para platina
        self.platina += self.ouro // 100
        self.ouro = self.ouro % 100

        self.save()
