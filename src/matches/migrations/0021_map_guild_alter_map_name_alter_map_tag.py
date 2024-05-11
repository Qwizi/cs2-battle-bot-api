# Generated by Django 5.0.6 on 2024-05-09 20:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guilds', '0004_remove_guild_members'),
        ('matches', '0020_remove_match_clinch_series_remove_match_map_sides_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='map',
            name='guild',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='maps', to='guilds.guild'),
        ),
        migrations.AlterField(
            model_name='map',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='map',
            name='tag',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
