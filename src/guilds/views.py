from rest_framework import viewsets
from rest_framework.decorators import action

from guilds.models import Guild
from guilds.serializers import GuildSerializer
from guilds.utils import create_guild, add_guild_member


class GuildViewSet(viewsets.ModelViewSet):
    queryset = Guild.objects.all()
    serializer_class = GuildSerializer

    def create(self, request, *args, **kwargs):
        return create_guild(request)

    @action(detail=True, methods=["post"])
    def add_member(self, request, pk=None):
        guild = self.get_object()
        return add_guild_member(guild, request)
