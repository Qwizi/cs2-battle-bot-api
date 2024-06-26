# Generated by Django 5.0.4 on 2024-04-04 14:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guilds', '0002_guild_lobby_channel_guild_team1_channel_and_more'),
        ('servers', '0002_alter_server_matches'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='guild',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='servers', to='guilds.guild'),
        ),
        migrations.AddField(
            model_name='server',
            name='is_public',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='server',
            name='password',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
