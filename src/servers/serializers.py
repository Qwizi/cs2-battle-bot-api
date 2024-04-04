from rest_framework import serializers
from players.serializers import TeamSerializer
from servers.models import Server


class ServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Server
        fields = ["id", "name", "ip", "port", "password", "is_public"]

    
class CreateMatchSerializer(serializers.Serializer):
    team_one_id = serializers.CharField(required=True)
    team_two_id = serializers.CharField(required=True)