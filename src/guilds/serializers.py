from rest_framework import serializers

from guilds.models import Guild


class GuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guild
        fields = "__all__"


class CreateGuildMemberSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    username = serializers.CharField()


class CreateGuildSerializer(serializers.Serializer):
    name = serializers.CharField()
    guild_id = serializers.CharField()
    owner_id = serializers.CharField()
    owner_username = serializers.CharField()
    members = CreateGuildMemberSerializer(many=True)