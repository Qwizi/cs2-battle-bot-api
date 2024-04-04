from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from guilds.models import Guild
from guilds.serializers import GuildSerializer, CreateGuildSerializer

UserModel = get_user_model()

# Create your views here.

class GuildViewSet(viewsets.ModelViewSet):
    queryset = Guild.objects.all()
    serializer_class = GuildSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreateGuildSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        owner = get_object_or_404(UserModel, player__discord_user__user_id=serializer.validated_data["owner_id"])
        guild = Guild.objects.create(
            name=serializer.validated_data["name"],
            guild_id=serializer.validated_data["guild_id"],
            owner=owner
        )
        return Response(GuildSerializer(guild).data)