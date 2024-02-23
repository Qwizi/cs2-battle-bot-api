import io
import json
import random
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from matches.models import Match, MatchStatus
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer

from matches.serializers import CreateMatchSerializer, KnifeRoundWinnerSerializer, MatchSerializer
from players.models import DiscordUser, Player
from players.serializers import PlayerSerializer

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return MatchSerializer
        if self.action == 'create':
            return CreateMatchSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            discord_users_ids = serializer.validated_data.get("discord_users_ids")
            print(discord_users_ids)
            if not discord_users_ids:
                return Response({"message": "Discord users cannot be empty"}, status=400)
            try:
                discord_users_list = [DiscordUser.objects.get(user_id=discord_user) for discord_user in discord_users_ids]
                players_list: list[Player] = []
                for discord_user in discord_users_list:
                    player: Player = Player.objects.get(discord_user=discord_user)
                    if player.steam_user is None:
                        return Response({"message": f"Discord user {discord_user.username} has no connected player"}, status=400)
                    players_list.append(
                        player
                    )
                    
                # create teams
                random.shuffle(players_list)

                num_members = len(players_list)
                middle_index = num_members // 2
                team1_name = serializer.validated_data.get("team1_name", "Team 1")
                team2_name = serializer.validated_data.get("team2_name", "Team 2")
                maplist = serializer.validated_data.get("maplist", [
                    "de_mirage",
                    "de_overpass",
                    "de_inferno"
                ])
                team1_players_list = players_list[:middle_index]
                team2_players_list = players_list[middle_index:]


                team1_players = {}
                for player in team1_players_list:
                    player_steamid64 = str(player.steam_user.steamid64)  # Assuming player has a steam_user attribute
                    player_name = player.steam_user.username  # Assuming player has a steam_user attribute
                    team1_players[player_steamid64] = player_name

                team2_players = {}
                for player in team2_players_list:
                    player_steamid64 = str(player.steam_user.steamid64)
                    player_name = player.steam_user.username
                    team2_players[player_steamid64] = player_name
                print(team1_players)
                # team2_players = {str(player.steam_user.steamid64): player.steam_user.username for player in team2_players_list}



                num_maps = len(maplist)
                team1 = {
                    "name": team1_name,
                    "players": team1_players
                    
                }
                team2 =  {
                    "name": team2_name,
                    "players": team2_players
                }

                data = {
                    "team1": team1,
                    "team2": team2,
                    "maplist": maplist,
                    "num_maps": num_maps,
                    "map_sides": [
                        "team1_ct",
                        "team2_ct",
                        "knife"
                    ],
                    "clinch_series": True,
                    "players_per_team": 5,
                }
                cache.set("current_match", json.dumps(data), timeout=60*60*24*7)
                return Response(data, status=201)
            except DiscordUser.DoesNotExist as e:
                return Response({"message": f"Discord user {e} not exists"}, status=400)
            except Player.DoesNotExist as e:
                return Response({"message": f"Player {e} not exists"}, status=400)
        else:
            return Response(serializer.errors, status=400)
    @action(detail=False, methods=["GET"])
    def current(self, request):
        match_data = cache.get("current_match")
        if not match_data:
            return Response({"message": "No current match"}, status=404)
        return Response(json.loads(match_data), status=200)
    
    @action(detail=False, methods=["PUT"])
    def start_knife_round(self, request):
        match_data = cache.get("current_match")
        if not match_data:
            return Response({"message": "No current match"}, status=404)
        match_data = json.loads(match_data)
        match_data["knife_round"] = True
        cache.set("current_match", json.dumps(match_data), timeout=60*60*24*7)
        return Response({"message": "Knife round started"}, status=200)
    
    @action(detail=False, methods=["PUT"])
    def end_knife_round(self, request):
        serializer = KnifeRoundWinnerSerializer(data=request.data)
        if serializer.is_valid():
            match_data = cache.get("current_match")
            if not match_data:
                return Response({"message": "No current match"}, status=404)
            match_data = json.loads(match_data)
            match_data["knife_round"] = False
            match_data["knife_team_winner"] = "team1" if serializer.validated_data.get("winner") == "ct" else "team2"
            match_data["knife_team_winner_site"] = serializer.validated_data.get("site")
            if match_data["knife_team_winner"] == "team1" and match_data["knife_team_winner_site"] == "ct":
                match_data["ct"] = "team1"
                match_data["t"] = "team2"
            elif match_data["knife_team_winner"] == "team1" and match_data["knife_team_winner_site"] == "t":
                match_data["ct"] = "team2"
                match_data["t"] = "team1"
            elif match_data["knife_team_winner"] == "team2" and match_data["knife_team_winner_site"] == "ct":
                match_data["ct"] = "team2"
                match_data["t"] = "team1"
            elif match_data["knife_team_winner"] == "team2" and match_data["knife_team_winner_site"] == "t":
                match_data["ct"] = "team1"
                match_data["t"] = "team2"
            cache.set("current_match", json.dumps(match_data), timeout=60*60*24*7)
            return Response({"message": "Knife round ended"}, status=200)
        else:
            return Response(serializer.errors, status=400)

    @action(detail=False, methods=["PUT"])
    def start(self, request):
        match_data = cache.get("current_match")
        if not match_data:
            return Response({"message": "No current match"}, status=404)
        match_data = json.loads(match_data)
        match_data["status"] = MatchStatus.IN_PROGRESS
        cache.set("current_match", json.dumps(match_data), timeout=60*60*24*7)
        return Response({"message": "Match started"}, status=200)
    
    @action(detail=False, methods=["PUT"])
    def end(self, request):
        match_data = cache.get("current_match")
        if not match_data:
            return Response({"message": "No current match"}, status=404)
        match_data = json.loads(match_data)
        match_data["status"] = MatchStatus.FINISHED
        cache.set("current_match", json.dumps(match_data), timeout=60*60*24*7)
        return Response({"message": "Match ended"}, status=200)
    
    @action(detail=False, methods=["PUT"])
    def cancel(self, request):
        match_data = cache.get("current_match")
        if not match_data:
            return Response({"message": "No current match"}, status=404)
        match_data = json.loads(match_data)
        match_data["status"] = MatchStatus.CANCELLED
        cache.set("current_match", json.dumps(match_data), timeout=60*60*24*7)
        return Response({"message": "Match cancelled"}, status=200)
        
    # @action(detail=True, methods=["POST"])
    # def ban(self, request, pk=None):
    #     map_name = request.data.get("map_name")
    #     team = request.data.get("team")
    #     if not pk or not map_name:
    #         return Response({"message": "Invalid data."}, status=400)
    #     if not Match.objects.filter(id=pk).exists():
    #         return Response({"message": "Match not found."}, status=404)
    #     if not cache.get(f"match:{pk}"):
    #         return Response({"message": "Match not found."}, status=404)
    #     match_data = json.loads(cache.get(f"match:{pk}"))
    #     if map_name in match_data["banned_maps"]["ct"] or map_name in match_data["banned_maps"]["t"]:
    #         return Response({"message": "Map already banned."}, status=400)
    #     match_data["banned_maps"][team].append(map_name)
    #     match_data_cache = cache.set(f"match:{pk}", json.dumps(match_data), timeout=60*60*24*7)
    #     return Response({"message": "Map banned."}, status=200)
    
    # @action(detail=True, methods=["GET"])
    # def cache(self, request, pk=None):
    #     if not pk:
    #         return Response({"message": "Invalid data."}, status=400)
    #     if not Match.objects.filter(id=pk).exists():
    #         return Response({"message": "Match not found."}, status=404)
    #     if not cache.get(f"match:{pk}"):
    #         return Response({"message": "Match not found."}, status=404)
    #     match_data = json.loads(cache.get(f"match:{pk}"))
    #     return Response(match_data, status=200)

# @api_view(["POST"])
# def create_match(request):
#     # Create match logic

#     new_match = Match.objects.create(
#         status="pending",
#         type="competitive",
#         map="unknown",
#         winner="pending"
#     )
#     match_data = {
#         "banned_maps": [],
#     }
#     match_data_cache = cache.set(f"match:{new_match.id}", json.dumps(match_data), timeout=60*60*24*7)
#     print(cache.get(f"match:{new_match.id}"))
#     return Response({"message": "Match created."}, status=201)

# @api_view(["POST"])
# def ban_map(request):
#     # Ban map logic
#     match_id = request.data.get("match_id")
#     map_name = request.data.get("map_name")
#     if not match_id or not map_name:
#         return Response({"message": "Invalid data."}, status=400)
#     if not Match.objects.filter(id=match_id).exists():
#         return Response({"message": "Match not found."}, status=404)
#     if not cache.get(f"match:{match_id}"):
#         return Response({"message": "Match not found."}, status=404)
#     match_data = json.loads(cache.get(f"match:{match_id}"))
#     if map_name in match_data["banned_maps"]:
#         return Response({"message": "Map already banned."}, status=400)
#     match_data["banned_maps"].append(map_name)
#     match_data_cache = cache.set(f"match:{match_id}", json.dumps(match_data), timeout=60*60*24*7)
#     print(cache.get(f"match:{match_id}"))
#     return Response({"message": "Map banned."}, status=200)