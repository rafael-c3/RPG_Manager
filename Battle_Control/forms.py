from django import forms
from .models import Personagem

class PersonagemForm(forms.ModelForm):
    class Meta:
        model = Personagem
        fields = ['nome',  'tipo', 'level', 'vida', 'defesa', 'força', 'magia', 'mana', 'agilidade', 'resistencia', 'necro', 'sorte', 'imagem'] # Controla a ordem das coisas
        labels = {
            'nome': 'Nome',
            'tipo': 'Tipo',
            'level': 'Level',
            'vida': 'Vida',
            'defesa': 'Defesa',
            'força': 'Força',
            'magia': 'Magia',
            'mana': 'Mana',
            'agilidade': 'Agilidade',
            'resistencia': 'Resistencia',
            'necro': 'Necro',
            'sorte': 'Sorte',
            'imagem': 'Imagem',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.NumberInput(attrs={'class': 'form-number'}),
            'vida': forms.NumberInput(attrs={'class': 'form-number'}),
            'defesa': forms.NumberInput(attrs={'class': 'form-number'}),
            'força': forms.NumberInput(attrs={'class': 'form-number'}),
            'magia': forms.NumberInput(attrs={'class': 'form-number'}),
            'mana': forms.NumberInput(attrs={'class': 'form-number'}),
            'agilidade': forms.NumberInput(attrs={'class': 'form-number'}),
            'resistencia': forms.NumberInput(attrs={'class': 'form-number'}),
            'necro': forms.NumberInput(attrs={'class': 'form-number'}),
            'sorte': forms.NumberInput(attrs={'class': 'form-number'}),
            'imagem': forms.FileInput(attrs={'class': 'form-button'}),
        }
        