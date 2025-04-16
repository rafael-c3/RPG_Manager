from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Personagem(models.Model):
    Tipo_Personagem = [
        ('Aliado', 'Aliado'),
        ('Inimigo', 'Inimigo'),
    ]

    nome = models.CharField(max_length=20)
    tipo = models.CharField(max_length=10, choices=Tipo_Personagem, default='Aliado')
    level = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(999)])

    vida = models.DecimalField(max_digits=5, decimal_places=1)
    defesa = models.DecimalField(max_digits=5, decimal_places=1)
    armadura = models.DecimalField(max_digits=5, decimal_places=1)
    força = models.DecimalField(max_digits=5, decimal_places=1)
    magia = models.DecimalField(max_digits=5, decimal_places=1)
    mana = models.DecimalField(max_digits=5, decimal_places=1)
    agilidade = models.DecimalField(max_digits=5, decimal_places=1)
    resistencia = models.DecimalField(max_digits=5, decimal_places=1)
    necro = models.DecimalField(max_digits=5, decimal_places=1)
    sorte = models.DecimalField(max_digits=5, decimal_places=1)

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

    def curar(self, valor):
        self.vida += valor
        self.save()


    def __str__(self):
        return self.nome
    
class Item(models.Model):
    TIPO_ITEM = [
        ('arma', 'Arma'),
        ('escudo', 'Escudo'),
        ('poção', 'Poção'),
        ('outro', 'Outro'),
    ]
    nome = models.CharField(max_length=50)
    tipo = models.CharField(max_length=10, choices=TIPO_ITEM)
    descricao = models.TextField(blank=True)
    valor_efeito = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    atributo_afetado = models.CharField(max_length=20, choices=[
        ('vida', 'Vida'),
        ('mana', 'Mana'),
        ('força', 'Força'),
        ('defesa', 'Defesa'),
        ('armadura', 'Armadura'),
    ])

    def __str__(self):
        return self.nome

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
    ]

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
    )

    nome = models.CharField(max_length=50)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    atributo_afetado = models.CharField(max_length=20, choices=ATRIBUTOS)
    valor = models.DecimalField(max_digits=5, decimal_places=1)
    reversivel = models.BooleanField(default=True, help_text="Se marcado, o efeito será revertido ao ser removido.")

    def __str__(self):
        return f"{self.nome} ({self.tipo})"


class EfeitoAplicado(models.Model):
    personagem = models.ForeignKey(Personagem, on_delete=models.CASCADE, related_name='efeitos_aplicados')
    efeito = models.ForeignKey(Efeito, on_delete=models.CASCADE)
    ativo = models.BooleanField(default=True)
    valor_aplicado = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    def aplicar(self):
        atributo = self.efeito.atributo_afetado
        valor = self.efeito.valor
        setattr(self.personagem, atributo, getattr(self.personagem, atributo) + valor)
        self.valor_aplicado = valor
        self.personagem.save()
        self.save()

    def remover(self):
        if self.efeito.reversivel:
            atributo = self.efeito.atributo_afetado
            setattr(self.personagem, atributo, getattr(self.personagem, atributo) - self.valor_aplicado)
            self.personagem.save()
        self.ativo = False
        self.save()

    def __str__(self):
        return f"{self.efeito.nome} em {self.personagem.nome}"
