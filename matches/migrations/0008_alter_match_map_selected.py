# Generated by Django 5.0.2 on 2024-03-03 21:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0007_matchmapselected_match_map_selected"),
    ]

    operations = [
        migrations.AlterField(
            model_name="match",
            name="map_selected",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="matches_map_selected",
                to="matches.matchmapselected",
            ),
            preserve_default=False,
        ),
    ]