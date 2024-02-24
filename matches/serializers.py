from os import read
from matches.models import Map, Match, MatchStatus, MatchType
from rest_framework import serializers
import players

from players.serializers import TeamSerializer

class MapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = "__all__"

class CurrentMatchSerializer(serializers.Serializer):
    matchid = serializers.CharField()
    team1 = serializers.DictField()
    team2 = serializers.DictField()
    num_maps = serializers.IntegerField()
    maplist = serializers.ListField(child=serializers.CharField())
    map_sides = serializers.ListField(child=serializers.ChoiceField(choices=["team1_ct", "team2_ct", "team1_t", "team2_t", "knife"]))
    clinch_series = serializers.BooleanField()
    players_per_team = serializers.IntegerField()
    

class MatchSerializer(serializers.ModelSerializer):
    team1 = TeamSerializer(read_only=True)
    team2 = TeamSerializer(read_only=True)
    winner_team = TeamSerializer(read_only=True)
    maps = MapSerializer(many=True, read_only=True)

    current_match = CurrentMatchSerializer(read_only=True, source="curent_match")

    class Meta:
        model = Match
        fields = "__all__"
        deph = 1


class CreateMatchSerializer(serializers.Serializer):
    discord_users_ids = serializers.ListField(child=serializers.CharField())
    team1_id = serializers.CharField(required=False)
    team2_id = serializers.CharField(required=False)
    shuffle_players = serializers.BooleanField(required=False, default=True)
    match_type = serializers.ChoiceField(choices=MatchType.choices, default=MatchType.BO1)
    players_per_team = serializers.IntegerField(required=False, default=5)
    clinch_series = serializers.BooleanField(required=False, default=False)
    map_sides = serializers.ListField(child=serializers.ChoiceField(choices=["team1_ct", "team2_ct", "team1_t", "team2_t", "knife"]), required=False, default=["knife", "team1_ct", "team2_ct"])
    maplist = serializers.ListField(child=serializers.CharField(required=False), required=False)
    cvars = serializers.DictField(child=serializers.CharField(required=False), required=False)


class KnifeRoundWinnerSerializer(serializers.Serializer):
    winner = serializers.CharField()
    site = serializers.CharField()
    