from django.db import models

class Personagem(models.Model):
    Tipo_Personagem = [
        ('Aliado', 'Aliado'),
        ('Inimigo', 'Inimigo'),
    ]

    nome = models.CharField(max_length=20)
    tipo = models.CharField(max_length=10, choices=Tipo_Personagem, default='Aliado')
    level = models.IntegerField(max_length=3)

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