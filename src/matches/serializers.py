from enum import Enum
import re
from rest_framework import serializers

from guilds.serializers import GuildSerializer
from matches.models import Map, MapBan, MapPick, Match, MatchType, MatchStatus
from players.serializers import TeamSerializer, DiscordUserSerializer
from servers.serializers import ServerSerializer


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
        model = MapBan
        fields = "__all__"


class MatchMapSelectedSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    map = MapSerializer(read_only=True)

    class Meta:
        model = MapPick
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
    maps = MapSerializer(many=True, read_only=True)
    winner_team = TeamSerializer(read_only=True, allow_null=True)
    map_bans = MapBanSerializer(many=True, read_only=True)
    last_map_ban = MapBanSerializer(read_only=True, allow_null=True)
    map_picks = MatchMapSelectedSerializer(many=True, read_only=True)
    last_map_pick = MatchMapSelectedSerializer(read_only=True, allow_null=True)
    connect_command = serializers.CharField(
        read_only=True, source="get_connect_command"
    )
    load_match_command = serializers.CharField(
        read_only=True, source="get_load_match_command"
    )
    author = DiscordUserSerializer(read_only=True)
    server = ServerSerializer(read_only=True, required=False, allow_null=True)
    guild = GuildSerializer(read_only=True)

    class Meta:
        model = Match
        fields = "__all__"


class MatchUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=MatchStatus.choices, required=False)
    type = serializers.ChoiceField(choices=MatchType.choices, required=False)
    team1_id = serializers.CharField(required=False)
    team2_id = serializers.CharField(required=False)
    map_sides = serializers.ListField(
        child=serializers.ChoiceField(
            choices=["team1_ct", "team2_ct", "team1_t", "team2_t", "knife"], required=False
        ),
        required=False,
    )
    clinch_series = serializers.BooleanField(required=False)
    cvars = serializers.DictField(required=False)
    message_id = serializers.CharField(required=False)
    author_id = serializers.CharField(required=False)
    server_id = serializers.CharField(required=False)
    guild_id = serializers.CharField(required=False)


class CreateMatchSerializer(serializers.Serializer):
    discord_users_ids = serializers.ListField(child=serializers.CharField())
    author_id = serializers.CharField(required=True)
    server_id = serializers.CharField(required=False)
    guild_id = serializers.CharField(required=True)
    match_type = serializers.ChoiceField(
        choices=MatchType.choices, default=MatchType.BO1
    )
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


class InteractionUserSerializer(serializers.Serializer):
    interaction_user_id = serializers.CharField(required=True)


class MatchBanMapSerializer(InteractionUserSerializer):
    map_tag = serializers.CharField(required=True)


class MatchPickMapSerializer(MatchBanMapSerializer):
    pass


class MatchBanMapResultSerializer(serializers.Serializer):
    banned_map = serializers.SerializerMethodField(method_name="get_banned_map")
    next_ban_team = serializers.SerializerMethodField(method_name="get_next_ban_team")
    maps_left = serializers.ListField(child=serializers.CharField())
    map_bans_count = serializers.IntegerField()

    def get_banned_map(self, obj) -> MapSerializer:
        return MapSerializer(self.context["banned_map"]).data

    def get_next_ban_team(self, obj) -> TeamSerializer:
        return TeamSerializer(self.context["next_ban_team"]).data


class MatchPickMapResultSerializer(serializers.Serializer):
    picked_map = serializers.SerializerMethodField(method_name="get_picked_map")
    next_pick_team = serializers.SerializerMethodField(method_name="get_next_pick_team")
    maps_left = serializers.ListField(child=serializers.CharField())
    map_picks_count = serializers.IntegerField()

    def get_picked_map(self, obj) -> MapSerializer:
        return MapSerializer(self.context["picked_map"]).data

    def get_next_pick_team(self, obj) -> TeamSerializer:
        return TeamSerializer(self.context["next_pick_team"]).data

class MatchPlayerJoin(InteractionUserSerializer):
    pass
