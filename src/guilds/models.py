from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from prefix_id import PrefixIDField
from rest_framework_api_key.models import AbstractAPIKey

from players.models import DiscordUser, Player

UserModel = get_user_model()


# Create your models here.

class GuildManager(models.Manager):
    def create_guild(self, owner_id: str, owner_username: str, **kwargs):
        dc_owner_user, _ = DiscordUser.objects.get_or_create(user_id=owner_id, username=owner_username)
        player, _ = Player.objects.get_or_create(discord_user=dc_owner_user)
        owner_user, _ = UserModel.objects.get_or_create(username=owner_username)
        if not owner_user.player:
            owner_user.player = player
            owner_user.save()
        guild = self.create(owner=owner_user, **kwargs)
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
    lobby_channel = models.CharField(max_length=255, null=True, blank=True)
    team1_channel = models.CharField(max_length=255, null=True, blank=True)
    team2_channel = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
