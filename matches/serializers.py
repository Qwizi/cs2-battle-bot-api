from enum import Enum
import re
from matches.models import Map, Match, MatchMapBan, MatchMapSelected, MatchType
from rest_framework import serializers

from players.serializers import TeamSerializer


class MatchEventEnum(str, Enum):
    SERIES_START = "series_start"
    SERIES_END = "series_end"
    MAP_RESULT = "map_result"
    SIDE_PICKED = "side_picked"
    MAP_PICKED = "map_picked"
    MAP_VETOED = "map_vetoed"
    GOING_LIVE = "going_live"
    ROUND_END = "round_end"


class MapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = "__all__"


class MapBanSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    map = MapSerializer(read_only=True)

    class Meta:
        model = MatchMapBan
        fields = "__all__"


class MatchMapSelectedSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    map = MapSerializer(read_only=True)

    class Meta:
        model = MatchMapSelected
        fields = "__all__"


class MatchConfigSerializer(serializers.Serializer):
    matchid = serializers.CharField()
    team1 = serializers.DictField()
    team2 = serializers.DictField()
    num_maps = serializers.IntegerField()
    maplist = serializers.ListField(child=serializers.CharField())
    map_sides = serializers.ListField(
        child=serializers.ChoiceField(
            choices=["team1_ct", "team2_ct", "team1_t", "team2_t", "knife"]
        )
    )
    clinch_series = serializers.BooleanField()
    players_per_team = serializers.IntegerField()
    cvars = serializers.DictField(required=False)


class MatchSerializer(serializers.ModelSerializer):
    team1 = TeamSerializer(read_only=True)
    team2 = TeamSerializer(read_only=True)
    winner_team = TeamSerializer(read_only=True)
    maps = MapSerializer(many=True, read_only=True)

    config = MatchConfigSerializer(read_only=True, source="get_config")
    map_bans = MapBanSerializer(many=True, read_only=True)
    map_picks = MatchMapSelectedSerializer(many=True, read_only=True)
    connect_command = serializers.CharField(
        read_only=True, source="get_connect_command"
    )
    load_match_command = serializers.CharField(
        read_only=True, source="get_load_match_command"
    )

    class Meta:
        model = Match
        fields = "__all__"
        deph = 1


class CreateMatchSerializer(serializers.Serializer):
    discord_users_ids = serializers.ListField(child=serializers.CharField())
    match_type = serializers.ChoiceField(
        choices=MatchType.choices, default=MatchType.BO1
    )
    players_per_team = serializers.IntegerField(required=False, default=5)
    clinch_series = serializers.BooleanField(required=False, default=False)
    map_sides = serializers.ListField(
        child=serializers.ChoiceField(
            choices=["team1_ct", "team2_ct", "team1_t", "team2_t", "knife"]
        ),
        required=False,
        default=["knife", "knife", "knife"],
    )
    cvars = serializers.DictField(
        child=serializers.CharField(required=False), required=False
    )


class MatchTeamWrapperSerializer(serializers.Serializer):
    name = serializers.CharField()


class MatchPlayerSerializer(serializers.Serializer):
    steamid = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    stats = serializers.DictField(required=True)


class MatchMapResultTeamSerializer(serializers.Serializer):
    name = serializers.CharField()
    series_score = serializers.IntegerField()
    score = serializers.IntegerField()
    score_ct = serializers.IntegerField()
    score_t = serializers.IntegerField()
    players = serializers.ListField(child=MatchPlayerSerializer())


class MatchTeamWinnerSerializer(serializers.Serializer):
    side = serializers.CharField()
    team = serializers.CharField()


class MatchEventSerializer(serializers.Serializer):
    matchid = serializers.CharField(required=True)
    event = serializers.CharField(required=True)


class MatchEventGoingLiveSerializer(MatchEventSerializer):
    map_number = serializers.IntegerField(required=True)


class MatchEventSeriesEndSerializer(MatchEventSerializer):
    team1_series_score = serializers.IntegerField(required=True)
    team2_series_score = serializers.IntegerField(required=True)
    winner = MatchTeamWinnerSerializer(required=True)
    time_until_restore = serializers.IntegerField(required=True)


class MatchEventSeriesStartSerializer(MatchEventSerializer):
    num_maps = serializers.IntegerField(required=True)
    team1 = MatchTeamWrapperSerializer(required=True)
    team2 = MatchTeamWrapperSerializer(required=True)


class MatchEventMapResultSerializer(MatchEventSerializer):
    map_number = serializers.IntegerField(required=True)
    team1 = MatchMapResultTeamSerializer(required=True)
    team2 = MatchMapResultTeamSerializer(required=True)
    winner = MatchTeamWinnerSerializer(required=True)


class MatchBanMapSerializer(serializers.Serializer):
    team_id = serializers.CharField(required=True)
    map_tag = serializers.CharField(required=True)


class MatchPickMapSerializer(serializers.Serializer):
    team_id = serializers.CharField(required=True)
    map_tag = serializers.CharField(required=True)


class MatchPlayerJoin(serializers.Serializer):
    discord_user_id = serializers.CharField(required=True)
