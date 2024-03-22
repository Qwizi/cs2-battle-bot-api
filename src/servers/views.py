from rest_framework import viewsets
from rest_framework.decorators import action
from matches.serializers import MatchSerializer
from players.models import Team
from servers.models import Server
from servers.serializers import CreateMatchSerializer, ServerSerializer
from rest_framework.response import Response

class ServerViewSet(viewsets.ModelViewSet):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer

    @action(detail=False, methods=['POST'])
    def create_match(self, request, pk=None):
        servers = self.get_queryset()
        if not servers.exists():
            return Response({"message": "No servers available."}, status=400)
        
        server = servers.first()

        serializer = CreateMatchSerializer(data=request.data)
        if serializer.is_valid():
            team_one_id = serializer.validated_data.get("team_one_id")
            team_two_id = serializer.validated_data.get("team_two_id")
            try:
                team_one = Team.objects.get(pk=team_one_id)
                team_two = Team.objects.get(pk=team_two_id)
            except Team.DoesNotExist as e:
                return Response({"message": f"Team {e} not exists"}, status=400)
            print(serializer.validated_data)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)
        

