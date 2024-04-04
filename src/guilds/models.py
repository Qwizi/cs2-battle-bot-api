from django.conf import settings
from django.db import models
from prefix_id import PrefixIDField
from rest_framework_api_key.models import AbstractAPIKey

# Create your models here.


class Guild(models.Model):
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
