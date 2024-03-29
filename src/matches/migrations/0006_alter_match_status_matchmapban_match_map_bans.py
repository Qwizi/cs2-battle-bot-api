# Generated by Django 5.0.2 on 2024-03-03 18:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0005_alter_match_id'),
        ('players', '0004_alter_team_leader'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='status',
            field=models.CharField(choices=[('CREATED', 'Created'), ('STARTED', 'Started'), ('LIVE', 'Live'), ('FINISHED', 'Finished')], default='CREATED', max_length=255),
        ),
        migrations.CreateModel(
            name='MatchMapBan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('map', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='map_bans', to='matches.map')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='map_bans', to='players.team')),
            ],
        ),
        migrations.AddField(
            model_name='match',
            name='map_bans',
            field=models.ManyToManyField(related_name='matches_map_bans', to='matches.matchmapban'),
        ),
    ]
