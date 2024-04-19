from rest_framework import serializers
from servers.models import Server


class ServerSerializer(serializers.ModelSerializer):
    rcon_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Server
        fields = ["id", "name", "ip", "port", "password", "is_public", "rcon_password", "guild"]