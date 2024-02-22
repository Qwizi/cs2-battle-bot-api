
from curses.ascii import CAN
from random import choices
from django.db import models
from prefix_id import PrefixIDField

from players.models import Team

class MatchStatus(models.TextChoices):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"

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



class MatchPlayer(models.Model):
    
    id = PrefixIDField(primary_key=True, prefix="match_player")
    player = models.ForeignKey("players.Player", on_delete=models.CASCADE, related_name="matches_players")
    match = models.ForeignKey("matches.Match", on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    kills = models.IntegerField()
    deaths = models.IntegerField()
    assists = models.IntegerField()
    headshots = models.IntegerField()
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.id} - {self.player.username} - {self.match.id} - {self.team}>"


class MatchTeam(models.Model):

    id = PrefixIDField(primary_key=True, prefix="match_team")
    match = models.ForeignKey("matches.Match", on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    side = models.CharField(max_length=255, choices=TeamSide.choices, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
            return f"<{self.id} - {self.match.id} - {self.team}>"

# Create your models here.
class Match(models.Model):
    

    id = PrefixIDField(primary_key=True, prefix="match")
    status = models.CharField(max_length=255, choices=MatchStatus.choices, default=MatchStatus.PENDING)
    type = models.CharField(max_length=255, choices=MatchType.choices, default=MatchType.BO1)
    maps = models.CharField(max_length=255, choices=MatchMap.choices, default=MatchMap.MIRAGE)
    teams = models.ManyToManyField(Team, through=MatchTeam, related_name="matches")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.id} - {self.status} - {self.type} - {self.map} - {self.winner}>"