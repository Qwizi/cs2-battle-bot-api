from rest_framework import serializers

from guilds.models import Guild


class GuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guild
        fields = "__all__"


class CreateGuildSerializer(serializers.Serializer):

    name = serializers.CharField()
    guild_id = serializers.CharField()
    owner_id = serializers.CharField()
    owner_username = serializers.CharField()