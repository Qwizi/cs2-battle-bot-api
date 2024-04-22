import math

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from prefix_id import PrefixIDField
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse_lazy

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


class MatchManager(models.Manager):
    def create_match(self, **kwargs):
        maps = Map.objects.all()
        maplist = kwargs.pop("maplist", None)
        if not maplist:
            maplist = [map.tag for map in maps]
        print(maplist)
        map_sides = kwargs.pop("map_sides", ["knife", "knife", "knife"])
        match_type = kwargs.pop("type", MatchType.BO1)
        team1 = kwargs.pop("team1", None)
        team2 = kwargs.pop("team2", None)
        author = kwargs.pop("author", None)
        server = kwargs.pop("server", None)
        num_maps = kwargs.pop("num_maps", 1 if match_type == MatchType.BO1 else 3)
        cvars = kwargs.pop("cvars", None)
        request = kwargs.pop("request", None)
        players_list = team1.players.all() | team2.players.all()
        player_per_team = len(players_list) / 2
        players_per_team_rounded = math.ceil(player_per_team)
        match = self.create(
            **kwargs,
            type=match_type,
            team1=team1,
            team2=team2,
            maplist=maplist,
            map_sides=map_sides,
            num_maps=num_maps,
            players_per_team=players_per_team_rounded,
            server=server,
            author=author,
            cvars=cvars,
        )
        match.maps.set(maps)
        match.create_webhook_cvars(webhook_url=str(reverse_lazy("match-webhook", args=[match.pk], request=request)))
        match.save()
        return match

    def check_server_is_available_for_match(self, server):
        return not self.filter(
            Q(server=server) &
            (Q(status=MatchStatus.LIVE) | Q(status=MatchStatus.STARTED))
        ).exists()

# Create your models here.
class Match(models.Model):
    objects = MatchManager()

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
    last_map_ban = models.ForeignKey(MapBan, on_delete=models.CASCADE, related_name="matches_last_map_ban", null=True)
    last_map_pick = models.ForeignKey(MapPick, on_delete=models.CASCADE, related_name="matches_last_map_pick", null=True)
    num_maps = models.PositiveIntegerField(default=1)
    maplist = models.JSONField(null=True)
    map_sides = models.JSONField(null=True)
    clinch_series = models.BooleanField(default=False)
    cvars = models.JSONField(null=True)
    players_per_team = models.PositiveIntegerField(default=5)
    message_id = models.CharField(max_length=255, null=True)
    author = models.ForeignKey("players.DiscordUser", on_delete=models.CASCADE, related_name="matches", null=True)
    server = models.ForeignKey(
        "servers.Server", on_delete=models.CASCADE, related_name="matches", null=True
    )
    guild = models.ForeignKey("guilds.Guild", on_delete=models.CASCADE, related_name="matches", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def config_url(self):
        return f"{settings.HOST_URL}/api/matches/{self.pk}/config/"

    @property
    def webhook_url(self):
        return f"{settings.HOST_URL}/api/matches/webhook/"

    @property
    def api_key_header(self):
        return "Bearer"

    @property
    def load_match_command_name(self):
        return "matchzy_loadmatch_url"

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
        return "" if not self.server else self.server.get_connect_string()

    def get_author_token(self):
        return UserModel.objects.get(player__discord_user=self.author).get_token()

    def get_load_match_command(self):
        return f'{self.load_match_command_name} "{self.config_url}" "{self.api_key_header}" "{self.get_author_token()}"'

    def create_webhook_cvars(self, webhook_url: str):
        self.cvars = self.cvars or {}
        self.cvars.update({
            "matchzy_remote_log_url": webhook_url,
            "matchzy_remote_log_header_key": self.api_key_header,
            "matchzy_remote_log_header_value": self.get_author_token(),
        })

    def get_maps_tags(self):
        return [map.tag for map in self.maps.all()]

    def ban_map(self, team, map):
        map_ban = MapBan.objects.create(team=team, map=map)
        self.map_bans.add(map_ban)
        self.maps.remove(map)
        self.maplist.remove(map.tag)
        self.last_map_ban = map_ban
        self.save()
        return self

    def pick_map(self, team, map):
        map_pick = MapPick.objects.create(team=team, map=map)
        self.map_picks.add(map_pick)
        map_index = self.maplist.index(map.tag)
        self.maplist.pop(map_index)
        map_picks_count = self.map_picks.count()
        if map_picks_count == 1:
            self.maplist.insert(0, map.tag)
        else:
            self.maplist.insert(1, map.tag)
        self.last_map_pick = map_pick
        self.save()
        return self