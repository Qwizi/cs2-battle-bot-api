from calendar import c
import math
from token import STAR
from django.db import models
from django.dispatch import receiver
from prefix_id import PrefixIDField
from cs2_battle_bot import settings

from players.models import Team


class MatchStatus(models.TextChoices):
    CREATED = "CREATED"
    STARTED = "STARTED"
    LIVE = "LIVE"
    FINISHED = "FINISHED"


class MatchType(models.TextChoices):
    BO1 = "BO1"
    BO2 = "BO2"
    BO3 = "BO3"
    BO5 = "BO5"


class MatchMap(models.TextChoices):
    MIRAGE = "de_mirage"
    INFERNO = "de_inferno"
    NUKE = "de_nuke"
    VERTIGO = "de_vertigo"
    OVERPASS = "de_overpass"
    ANCIENT = "de_ancient"
    ANUBUS = "de_anubis"


class TeamSide(models.TextChoices):
    CT = "CT"
    T = "T"


class Map(models.Model):
    id = PrefixIDField(primary_key=True, prefix="map")
    name = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.name} - {self.tag} - {self.id}>"


class MatchMapBan(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="map_bans")
    map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name="map_bans")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.team.name} - {self.map.name}>"


class MatchMapSelected(models.Model):
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="map_selected"
    )
    map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name="map_selected")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.team.name} - {self.map.name}>"


# Create your models here.
class Match(models.Model):
    status = models.CharField(
        max_length=255, choices=MatchStatus.choices, default=MatchStatus.CREATED
    )
    type = models.CharField(
        max_length=255, choices=MatchType.choices, default=MatchType.BO1
    )
    maps = models.ManyToManyField(Map, related_name="matches_maps")
    team1 = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="matches_team1", null=True
    )
    team2 = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="matches_team2", null=True
    )
    winner_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="matches_winner", null=True
    )
    map_bans = models.ManyToManyField(MatchMapBan, related_name="matches_map_bans")
    map_picks = models.ManyToManyField(
        MatchMapSelected, related_name="matches_map_picks"
    )
    num_maps = models.PositiveIntegerField(default=1)
    maplist = models.JSONField(null=True)
    map_sides = models.JSONField(null=True)
    clinch_series = models.BooleanField(default=False)
    cvars = models.JSONField(null=True)
    players_per_team = models.PositiveIntegerField(default=5)
    cvars = models.JSONField(null=True)
    message_id = models.CharField(max_length=255, null=True)
    author_id = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.team1.name} vs {self.team2.name}- {self.status} - {self.type} - {self.pk}>"

    def get_team1_players_dict(self):
        return {
            "name": self.team1.name,
            "players": self.team1.get_players_dict(),
        }

    def get_team2_players_dict(self):
        return {
            "name": self.team2.name,
            "players": self.team2.get_players_dict(),
        }

    def get_config(self):
        config = {
            "matchid": self.pk,
            "team1": self.get_team1_players_dict(),
            "team2": self.get_team2_players_dict(),
            "num_maps": self.num_maps,
            "maplist": self.maplist,
            "map_sides": self.map_sides,
            "clinch_series": self.clinch_series,
            "players_per_team": self.players_per_team,
        }
        if self.cvars:
            config["cvars"] = self.cvars
        return config

    def get_connect_command(self):
        return f"connect {settings.RCON_HOST}:{settings.SERVER_PORT}; password {settings.SERVER_PASSWORD};"

    def get_load_match_command(self):
        api_key_header = '"X-Api-Key"'
        api_key = f'"{settings.API_KEY}"'
        match_url = f'"{settings.HOST_URL}/api/matches/{self.pk}/config/"'
        return f"matchzy_loadmatch_url {match_url} {api_key_header} {api_key}"
