# Generated by Django 5.0.4 on 2024-04-21 14:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0004_alter_team_leader'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='steam_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='players.steamuser'),
        ),
    ]
