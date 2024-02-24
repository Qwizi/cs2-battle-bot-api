from players.models import DiscordUser, Player, SteamUser, Team
from rest_framework import serializers

class DiscordUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordUser
        fields = '__all__'


class SteamUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SteamUser
        fields = '__all__'

class PlayerSerializer(serializers.ModelSerializer):
    discord_user = DiscordUserSerializer(read_only=True)
    steam_user = SteamUserSerializer(read_only=True)
    class Meta:
        model = Player
        fields = '__all__'
        depth = 1

class TeamSerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True, read_only=True)
    class Meta:
        model = Team
        fields = '__all__'