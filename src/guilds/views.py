from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action

from guilds.models import Guild
from guilds.serializers import GuildSerializer, CreateGuildSerializer, CreateGuildMemberSerializer
from guilds.utils import create_guild, add_guild_member


class GuildViewSet(viewsets.ModelViewSet):
    queryset = Guild.objects.all().order_by("created_at")
    serializer_class = GuildSerializer

    @extend_schema(
        request=CreateGuildSerializer,
        responses={201: GuildSerializer}
    )
    def create(self, request, *args, **kwargs):
        return create_guild(request)

    @extend_schema(
        request=CreateGuildMemberSerializer,
        responses={200: GuildSerializer}
    )
    @action(detail=True, methods=["post"])
    def add_member(self, request, pk=None):
        guild = self.get_object()
        return add_guild_member(guild, request)
