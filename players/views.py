from rest_framework import viewsets
from players.models import Player, Team
from players.serializers import PlayerSerializer, TeamSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    @action(detail=True, methods=['POST'])
    def add_player(self, request, pk=None):
        try:
            team = self.get_object()
            player = Player.objects.get(id=request.data['player_id'])
            team.players.add(player)
            team.save()
        except Player.DoesNotExist as e:
            return Response({'status': f'Player {e} not exists'}, status=400)
        else:
            return Response({'status': 'player added'})
    
    @action(detail=True, methods=['POST'])
    def remove_player(self, request, pk=None):
        try:
            team = self.get_object()
            player = Player.objects.get(id=request.data['player_id'])
            team.players.remove(player)
            team.save()
        except Player.DoesNotExist as e:
            return Response({'status': f'Player {e} not exists'}, status=400)
        else:
            return Response({'status': 'player removed'})
    
    @action(detail=True, methods=['POST'])
    def set_leader(self, request, pk=None):
        try:
            team = self.get_object()
            player = Player.objects.get(id=request.data['player_id'])
            team.leader = player
            team.save()
        except Player.DoesNotExist as e:
            return Response({'status': f'Player {e} not exists'}, status=400)
        else:
            return Response({'status': 'leader set'})
    
    @action(detail=True, methods=['POST'])
    def remove_leader(self, request, pk=None):
        try:
            team = self.get_object()
            team.leader = team.players.first()
            team.save()
        except Player.DoesNotExist as e:
            return Response({'status': f'Player {e} not exists'}, status=400)
        else:
            return Response({'status': 'leader removed'})