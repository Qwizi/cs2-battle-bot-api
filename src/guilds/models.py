from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from prefix_id import PrefixIDField
from rest_framework_api_key.models import AbstractAPIKey

from players.models import DiscordUser

UserModel = get_user_model()


# Create your models here.

class GuildManager(models.Manager):
    def create_guild(self, owner_id: str, owner_username: str, members: list[dict], **kwargs):
        dc_owner_user, _ = DiscordUser.objects.get_or_create(user_id=owner_id, username=owner_username)
        owner_user, _ = UserModel.objects.get_or_create(username=owner_username)
        guild_discord_members = []
        for member in members:
            dc_user, _ = DiscordUser.objects.get_or_create(user_id=member["user_id"], username=member["username"])
            guild_discord_members.append(dc_user)
        for member in guild_discord_members:
            user, _ = UserModel.objects.get_or_create(username=member.username)
        guild = self.create(owner=owner_user, **kwargs)
        guild_discord_members.append(dc_owner_user)
        guild.members.set(guild_discord_members)
        guild.save()
        return guild


class Guild(models.Model):
    objects = GuildManager()
    id = PrefixIDField(primary_key=True, prefix="guild")
    name = models.CharField(max_length=255)
    guild_id = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guild_owner"
    )
    members = models.ManyToManyField("players.DiscordUser", related_name="guild_members")
    lobby_channel = models.CharField(max_length=255, null=True, blank=True)
    team1_channel = models.CharField(max_length=255, null=True, blank=True)
    team2_channel = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
