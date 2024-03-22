from django.db import models
from prefix_id import PrefixIDField


class Server(models.Model):
    id = PrefixIDField(primary_key=True, prefix="server")
    ip = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    port = models.PositiveIntegerField()
    rcon_password = models.CharField(max_length=100)
    max_players = models.PositiveIntegerField()
    matches = models.ManyToManyField(
        "matches.Match", related_name="servers", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.ip}:{self.port} - {self.name}>"
