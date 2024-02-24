from enum import unique
from django.db import models
from prefix_id import PrefixIDField

# Create your models here.
class DiscordUser(models.Model):
    
    id = PrefixIDField(primary_key=True, prefix="dc_user")
    user_id = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.username} - {self.user_id} - {self.id}>"

class SteamUser(models.Model):
    id = PrefixIDField(primary_key=True, prefix="steam_user")
    username = models.CharField(max_length=255)
    steamid64 = models.CharField(max_length=255, null=True)
    steamid32 = models.CharField(max_length=255, null=True)
    profile_url = models.CharField(max_length=255, null=True)
    avatar = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.username} - {self.steamid64} - {self.id}>"

class Player(models.Model):
    id = PrefixIDField(primary_key=True, prefix="player")
    discord_user = models.ForeignKey(DiscordUser, on_delete=models.CASCADE)
    steam_user = models.ForeignKey(SteamUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.discord_user.username} - {self.steam_user.username} - {self.id}>"
    
    def get_player_dict(self):
        return {str(self.steam_user.steamid64): self.steam_user.username}
    
class Team(models.Model):
    id = PrefixIDField(primary_key=True, prefix="team")
    name = models.CharField(max_length=255, unique=True)
    players = models.ManyToManyField("players.Player", related_name="teams")
    leader = models.ForeignKey("players.Player", on_delete=models.CASCADE, related_name="team_leader", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return f"<{self.name} - {self.id}>"
