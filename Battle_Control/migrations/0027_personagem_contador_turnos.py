# Generated by Django 5.2 on 2025-04-19 00:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Battle_Control', '0026_remove_personagem_passiva'),
    ]

    operations = [
        migrations.AddField(
            model_name='personagem',
            name='contador_turnos',
            field=models.IntegerField(default=0),
        ),
    ]
