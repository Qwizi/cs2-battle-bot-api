from pkg_resources import require
from matches.models import Match
from rest_framework import serializers

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = "__all__"


class CreateMatchSerializer(serializers.Serializer):
    discord_users_ids = serializers.ListField(child=serializers.CharField())
    team1_name = serializers.CharField(required=False)
    team2_name = serializers.CharField(required=False)
    map_list = serializers.ListField(child=serializers.CharField(required=False), required=False)


class KnifeRoundWinnerSerializer(serializers.Serializer):
    winner = serializers.CharField()
    site = serializers.CharField()
    