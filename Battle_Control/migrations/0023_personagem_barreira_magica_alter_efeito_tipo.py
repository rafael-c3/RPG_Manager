# Generated by Django 5.2 on 2025-04-18 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Battle_Control', '0022_alter_item_tipo'),
    ]

    operations = [
        migrations.AddField(
            model_name='personagem',
            name='barreira_magica',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='efeito',
            name='tipo',
            field=models.CharField(choices=[('buff', 'Buff'), ('debuff', 'Debuff'), ('passiva', 'Passiva'), ('arma', 'Arma')], max_length=10),
        ),
    ]
