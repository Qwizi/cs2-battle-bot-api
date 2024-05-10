from rest_framework import serializers

from matches.models import MatchStatus
from players.models import DiscordUser


class ValidDiscordUser(object):

    def __call__(self, value):
        if not DiscordUser.objects.filter(user_id=value).exists():
            raise serializers.ValidationError(f"DiscordUser @<{value}> does not exist")


class DiscordUserCanJoinMatch(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        match = serializer_field.context.get("match")
        if match.status != MatchStatus.CREATED:
            raise serializers.ValidationError("Match is not in CREATED status")

        if match.team1.players.filter(discord_user__user_id=value).exists() or match.team2.players.filter(
                discord_user__user_id=value).exists():
            raise serializers.ValidationError(f"DiscordUser @<{value}> is already in a match")

        if (match.team1.players.count() + match.team2.players.count()) >= match.config.max_players:
            raise serializers.ValidationError("Match is full")

        if match.author.user_id == value:
            raise serializers.ValidationError(f"DiscordUser @<{value}> is author of the match and cannot join")


class TeamCanBeJoined(object):
    requires_context = True

    def __init__(self, interaction_user_id):
        self.interaction_user_id = interaction_user_id

    def __call__(self, value, serializer_field):
        if value not in ["team1", "team2"]:
            raise serializers.ValidationError("Team must be either 'team1' or 'team2'")

        match = serializer_field.context.get("match")

        if value == "team1" and match.team1.players.count() >= match.config.max_players // 2:
            raise serializers.ValidationError("Team1 is full")
        if value == "team2" and match.team2.players.count() >= match.config.max_players // 2:
            raise serializers.ValidationError("Team2 is full")
        if match.team1.players.filter(discord_user__user_id=self.interaction_user_id).exists() or \
                match.team2.players.filter(discord_user__user_id=self.interaction_user_id).exists():
            raise serializers.ValidationError("Player is already in a team")


class DiscordUserCanLeaveMatch(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        match = serializer_field.context.get("match")
        if match.status != MatchStatus.CREATED:
            raise serializers.ValidationError("Match is not in CREATED status")

        if not match.team1.players.filter(discord_user__user_id=value).exists() and not match.team2.players.filter(
                discord_user__user_id=value).exists():
            raise serializers.ValidationError(f"DiscordUser @<{value}> is not in a match")

        if match.author.user_id == value:
            raise serializers.ValidationError(f"DiscordUser @<{value}> is author of the match and cannot leave")
