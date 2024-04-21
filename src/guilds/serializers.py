from rest_framework import serializers

from accounts.serializers import UserSerializer
from guilds.models import Guild


class GuildSerializer(serializers.ModelSerializer):

    owner = UserSerializer(read_only=True)

    class Meta:
        model = Guild
        fields = "__all__"


class CreateGuildSerializer(serializers.Serializer):
    name = serializers.CharField()
    guild_id = serializers.CharField()
    owner_id = serializers.CharField()
    owner_username = serializers.CharField()


class UpdateGuildSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    lobby_channel = serializers.CharField(required=False)
    team1_channel = serializers.CharField(required=False)
    team2_channel = serializers.CharField(required=False)