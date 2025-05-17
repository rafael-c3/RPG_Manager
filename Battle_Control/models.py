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
    level = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(999)])

    vida = models.DecimalField(max_digits=5, decimal_places=1)
    vida_maxima = models.DecimalField(max_digits=5, decimal_places=1)
    defesa = models.DecimalField(max_digits=5, decimal_places=1)
    armadura = models.DecimalField(max_digits=5, decimal_places=1)
    força = models.DecimalField(max_digits=5, decimal_places=1)
    magia = models.DecimalField(max_digits=5, decimal_places=1)
    mana = models.DecimalField(max_digits=5, decimal_places=1)
    agilidade = models.DecimalField(max_digits=5, decimal_places=1)
    resistencia = models.DecimalField(max_digits=5, decimal_places=1)
    necro = models.DecimalField(max_digits=5, decimal_places=1)
    sorte = models.DecimalField(max_digits=5, decimal_places=1)

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
