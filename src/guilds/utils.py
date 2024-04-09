from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from guilds.models import Guild
from guilds.serializers import GuildSerializer, CreateGuildSerializer, CreateGuildMemberSerializer
from players.models import DiscordUser, Player

UserModel = get_user_model()


def create_discord_user(user_id: str, username: str) -> DiscordUser:
    try:
        discord_user = DiscordUser.objects.get(user_id=user_id)
    except DiscordUser.DoesNotExist:
        discord_user = DiscordUser.objects.create(
            user_id=user_id,
            username=username
        )
    return discord_user


def create_player(discord_user: DiscordUser) -> Player:
    try:
        player = Player.objects.get(discord_user=discord_user)
    except Player.DoesNotExist:
        player = Player.objects.create(
            discord_user=discord_user
        )
    return player


def create_user(discord_user_id: str, discord_username: str) -> UserModel:
    discord_user = create_discord_user(discord_user_id, discord_username)
    try:
        user = UserModel.objects.get(username=discord_username)
    except UserModel.DoesNotExist:
        user = UserModel.objects.create(
            username=discord_username
        )
    return user, discord_user


def create_members(members: list[CreateGuildMemberSerializer]) -> list[DiscordUser]:
    return [create_discord_user(member.validated_data["user_id"], member.validated_data["username"]) for member in
            members]


def create_guild(request) -> Response["GuildSerializer"]:
    serializer = CreateGuildSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    owner_id = serializer.validated_data["owner_id"]
    owner_username = serializer.validated_data["owner_username"]
    members = serializer.validated_data["members"]

    owner, dc_user = create_user(owner_id, owner_username)
    users = [create_user(member["user_id"], member["username"]) for member in members]
    dc_users = [dc_user for user, dc_user in users]
    dc_users.append(dc_user)
    guild = Guild.objects.create(
        name=serializer.validated_data["name"],
        guild_id=serializer.validated_data["guild_id"],
        owner=owner,
    )
    guild.members.set(dc_users)
    return Response(GuildSerializer(guild).data)


def add_guild_member(guild: Guild, request) -> Response["GuildSerializer"]:
    serializer = CreateGuildMemberSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user_id = serializer.validated_data["user_id"]
    username = serializer.validated_data["username"]
    dc_user = get_object_or_404(DiscordUser, user_id=user_id, username=username)
    guild.members.add(dc_user)
    guild.save()
    return Response(GuildSerializer(guild).data)
