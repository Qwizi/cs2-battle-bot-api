

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from prefix_id import PrefixIDField
from rest_framework.authtoken.models import Token

from players.models import Team

UserModel = get_user_model()

class MatchStatus(models.TextChoices):
    CREATED = "CREATED"
    STARTED = "STARTED"
    LIVE = "LIVE"
    FINISHED = "FINISHED"


class MatchType(models.TextChoices):
    BO1 = "BO1"
    BO3 = "BO3"
    BO5 = "BO5"


class Map(models.Model):
    id = PrefixIDField(primary_key=True, prefix="map")
    name = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.name} - {self.tag} - {self.id}>"


class MapBan(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="map_bans")
    map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name="map_bans")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.team.name} - {self.map.name}>"


class MapPick(models.Model):
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
    map_bans = models.ManyToManyField(MapBan, related_name="matches_map_bans")
    map_picks = models.ManyToManyField(
        MapPick, related_name="matches_map_picks"
    )
    num_maps = models.PositiveIntegerField(default=1)
    maplist = models.JSONField(null=True)
    map_sides = models.JSONField(null=True)
    clinch_series = models.BooleanField(default=False)
    cvars = models.JSONField(null=True)
    players_per_team = models.PositiveIntegerField(default=5)
    cvars = models.JSONField(null=True)
    message_id = models.CharField(max_length=255, null=True)
    author = models.ForeignKey("players.DiscordUser", on_delete=models.CASCADE, related_name="matches", null=True)
    server = models.ForeignKey(
        "servers.Server", on_delete=models.CASCADE, related_name="matches", null=True
    )
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
        if not self.server:
            return ""
        return self.server.get_connect_string()

    def get_load_match_command(self):
        api_key_header = '"Bearer"'
        user = UserModel.objects.get(player__discord_user=self.author)
        token = Token.objects.get(user=user)
        api_key = f'"{token.key}"'
        match_url = f'"{settings.HOST_URL}/api/matches/{self.pk}/config/"'
        return f"matchzy_loadmatch_url {match_url} {api_key_header} {api_key}"
