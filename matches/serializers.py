from matches.models import Match
from rest_framework import serializers

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = "__all__"


class CreateMatchSerializer(serializers.Serializer):
    discord_users_ids = serializers.ListField(child=serializers.CharField())


class KnifeRoundWinnerSerializer(serializers.Serializer):
    winner = serializers.CharField()
    site = serializers.CharField()
    