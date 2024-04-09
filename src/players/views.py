from rest_framework import viewsets
from players.models import Player, Team, DiscordUser, SteamUser
from players.serializers import PlayerSerializer, TeamSerializer, DiscordUserSerializer, SteamUserSerializer


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer


class DiscordUserViewSet(viewsets.ModelViewSet):
    queryset = DiscordUser.objects.all()
    serializer_class = DiscordUserSerializer


class SteamUserViewSet(viewsets.ModelViewSet):
    queryset = SteamUser.objects.all()
    serializer_class = SteamUserSerializer


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
