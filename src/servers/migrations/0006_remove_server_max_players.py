# Generated by Django 5.0.4 on 2024-04-13 16:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0005_alter_server_guild_alter_server_rcon_password'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='server',
            name='max_players',
        ),
    ]
