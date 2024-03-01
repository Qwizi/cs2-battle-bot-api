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


class Map(models.Model):
    id = PrefixIDField(primary_key=True, prefix="map")
    name = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.name} - {self.tag} - {self.id}>"


# Create your models here.
class Match(models.Model):
    status = models.CharField(
        max_length=255, choices=MatchStatus.choices, default=MatchStatus.PENDING
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.team1.name} vs {self.team2.name}- {self.status} - {self.type} - {self.id}>"
