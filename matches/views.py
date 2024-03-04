import json
from random import shuffle
from django.conf import settings
from rcon import EmptyResponse, SessionTimeout, WrongPassword
import redis
from rcon.source import Client

from rest_framework.response import Response
from django.core.cache import cache
from matches.models import (
    Map,
    Match,
    MatchMapBan,
    MatchMapSelected,
    MatchStatus,
    MatchType,
)
from rest_framework import viewsets
from rest_framework.decorators import action

from matches.serializers import (
    CreateMatchSerializer,
    MapSerializer,
    MatchBanMapSerializer,
    MatchEventEnum,
    MatchEventGoingLiveSerializer,
    MatchEventMapResultSerializer,
    MatchEventSerializer,
    MatchEventSeriesEndSerializer,
    MatchEventSeriesStartSerializer,
    MatchMapSelectedSerializer,
    MatchPickMapSerializer,
    MatchSerializer,
)
from players.models import DiscordUser, Player, Team


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

    def publish_event(self, event, data):
        redis_client = redis.StrictRedis(host="redis", port=6379, db=0)
        redis_client.publish("event.going_live", json.dumps(data))

    def __divide_players(
        self, players_list: list[Player]
    ) -> tuple[list[Player], list[Player]]:
        """
        Divide a list of players into two lists.

        Args:
        -----
            players_list (list[Player]): List of players.

        Returns:
        --------
            tuple[list[Player], list[Player]]: Tuple with two lists of players.

        """
        shuffle(players_list)
        num_members = len(players_list)
        middle_index = num_members // 2
        return players_list[:middle_index], players_list[middle_index:]

    def __create_default_teams(
        self, team1_name: str, team2_name: str, players_list: list[Player]
    ) -> tuple[Team, Team]:
        """
        Create two teams with the given players.

        Args:
        -----
            team1_name (str): Name of the first team.
            team2_name (str): Name of the second team.
            team1_players_list (list[Player]): List of players for the first team.
            team2_players_list (list[Player]): List of players for the second team.

        Returns:
        --------
            tuple[Team, Team]: Tuple with two teams.

        """
        team1 = Team.objects.get_or_create(name=team1_name)[0]
        team2 = Team.objects.get_or_create(name=team2_name)[0]
        team1_players_list, team2_players_list = self.__divide_players(players_list)

        team1.players.set(team1_players_list)
        team1.leader = team1_players_list[0]
        team1.save()

        team2.players.set(team2_players_list)
        team2.leader = team2_players_list[0]
        team2.save()
        return team1, team2

    def __send_rcon_command(self, command: str, *args):
        """
        Send an RCON command to the server.

        Args:
        -----
            command (str): RCON command.

        Returns:
        --------
            None

        """
        try:
            with Client(
                settings.RCON_HOST,
                int(settings.RCON_PORT),
                passwd=settings.RCON_PASSWORD,
            ) as client:
                return client.run(command, *args)
        except (EmptyResponse, SessionTimeout, WrongPassword) as e:
            print(f"Error sending RCON command: {e}")
            return None

    def create(self, request, *args, **kwargs):
        serializer = CreateMatchSerializer(data=request.data)
        if serializer.is_valid():
            discord_users_ids = serializer.validated_data.get("discord_users_ids")
            team1_id = serializer.validated_data.get("team1_id", None)
            team2_id = serializer.validated_data.get("team2_id", None)
            shuffle_players = serializer.validated_data.get("shuffle_players", True)
            match_type = serializer.validated_data.get("match_type", "BO1")
            players_per_team = serializer.validated_data.get("players_per_team", 5)
            clinch_series = serializer.validated_data.get("clinch_series", False)
            map_sides = serializer.validated_data.get(
                "map_sides", ["knife", "team1_ct", "team2_ct"]
            )
            # maplist = serializer.validated_data.get("maplist", None)
            cvars = serializer.validated_data.get("cvars", None)
            # Remove duplicates from discord_users_ids
            discord_users_ids = list(set(discord_users_ids))
            if not discord_users_ids:
                return Response(
                    {"message": "Discord users cannot be empty"}, status=400
                )
            try:
                discord_users_list = []
                try:
                    for discord_user_id in discord_users_ids:
                        discord_user = DiscordUser.objects.get(user_id=discord_user_id)
                        discord_users_list.append(discord_user)
                except DiscordUser.DoesNotExist as e:
                    return Response(
                        {
                            "message": f"Discord user {discord_user_id} not exists",
                            "user_id": discord_user_id,
                        },
                        status=400,
                    )
                players_list: list[Player] = []
                for discord_user in discord_users_list:
                    player: Player = Player.objects.get(discord_user=discord_user)
                    if player.steam_user is None:
                        return Response(
                            {
                                "message": f"Discord user {discord_user.username} has no connected player"
                            },
                            status=400,
                        )
                    players_list.append(player)

                team1, team2 = None, None
                team1_players, team2_players = {}, {}

                if len(players_list) < 2:
                    return Response(
                        {"message": "At least 2 players are required"}, status=400
                    )

                if shuffle_players:
                    team1, team2 = self.__create_default_teams(
                        "Team 1", "Team 2", players_list
                    )
                    team1_players = {
                        str(player.steam_user.steamid64): player.steam_user.username
                        for player in team1.players.all()
                    }
                    team2_players = {
                        str(player.steam_user.steamid64): player.steam_user.username
                        for player in team2.players.all()
                    }
                else:
                    if not team1_id or not team2_id:
                        return Response(
                            {"message": "team1_id and team2_id ids are required"},
                            status=400,
                        )
                    try:
                        team1 = Team.objects.get(id=team1_id)
                        team2 = Team.objects.get(id=team2_id)
                        players_ids = [player.id for player in players_list]
                        team1_players = {
                            str(player.steam_user.steamid64): player.steam_user.username
                            for player in team1.players.filter(pk__in=players_ids)
                        }
                        team2_players = {
                            str(player.steam_user.steamid64): player.steam_user.username
                            for player in team2.players.filter(pk__in=players_ids)
                        }
                    except Team.DoesNotExist as e:
                        return Response({"message": f"Team {e} not exists"}, status=400)
                maps = Map.objects.all()
                num_maps = 1
                if match_type == "BO3":
                    num_maps = 3
                else:
                    num_maps = 1

                new_match = Match.objects.create(
                    type=match_type,
                    team1=team1,
                    team2=team2,
                )

                new_match.maps.set(maps)
                new_match.save()

                current_match_data = {
                    "matchid": new_match.id,
                    "team1": {"name": team1.name, "players": team1_players},
                    "team2": {"name": team2.name, "players": team2_players},
                    "num_maps": num_maps,
                    "maplist": [map.tag for map in maps],
                    "map_sides": map_sides,
                    "clinch_series": clinch_series,
                    "players_per_team": players_per_team,
                }
                if cvars:
                    current_match_data["cvars"] = cvars
                new_match_serializer = MatchSerializer(new_match)

                cache.set(
                    "current_match",
                    json.dumps(current_match_data),
                    timeout=60 * 60 * 24 * 7,
                )

                return Response(new_match_serializer.data, status=201)
            # except DiscordUser.DoesNotExist as e:
            #     return Response({"message": f"Discord user {e} not exists"}, status=400)
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

    @action(detail=True, methods=["POST"])
    def set_teams(self, request, pk=None):
        try:
            match = self.get_object()
            team1_id = request.data.get("team1_id")
            team2_id = request.data.get("team2_id")
            team1 = Team.objects.get(id=team1_id)
            team2 = Team.objects.get(id=team2_id)
            match.team1 = team1
            match.team2 = team2
            match.save()
        except Team.DoesNotExist as e:
            return Response({"message": f"Team {e} not exists"}, status=400)
        else:
            return Response({"message": "teams set"})

    @action(detail=False, methods=["POST"])
    def load(self, request):
        match_data = cache.get("current_match")
        if not match_data:
            return Response({"message": "No current match"}, status=404)
        match = json.loads(match_data)
        match_id = match.get("matchid")
        try:
            match = Match.objects.get(id=match_id)
        except Match.DoesNotExist:
            return Response(
                {"message": f"Match with id {match_id} not exists"}, status=400
            )
        api_key_header = '"X-Api-Key"'
        api_key = f'"{settings.API_KEY}"'
        load_match_command = "matchzy_loadmatch_url"
        match_url = f'"{settings.HOST_URL}/api/matches/current/"'

        self.__send_rcon_command(load_match_command, match_url, api_key_header, api_key)
        return Response({"status": "match config loaded"})

    @action(detail=False, methods=["POST"])
    def webhook(self, request):
        match_event_serializer = MatchEventSerializer(data=request.data)
        if not match_event_serializer.is_valid():
            return Response(match_event_serializer.errors, status=400)
        match_id = match_event_serializer.validated_data.get("matchid")
        try:
            match = Match.objects.get(
                id=match_event_serializer.validated_data.get("matchid")
            )
        except Match.DoesNotExist:
            return Response(
                {"status": f"Match with id {match_id} not exists"}, status=400
            )
        data = None
        redis_event = None
        match match_event_serializer.validated_data.get("event"):
            case MatchEventEnum.SERIES_START:
                series_start_serializer = MatchEventSeriesStartSerializer(
                    data=request.data
                )
                if not series_start_serializer.is_valid():
                    return Response(series_start_serializer.errors, status=400)
                data = series_start_serializer.validated_data
                match.status = MatchStatus.STARTED
                match.save()
                redis_event = f"event.{MatchEventEnum.SERIES_START.value}"
            case MatchEventEnum.SERIES_END:
                series_end_serializer = MatchEventSeriesEndSerializer(data=request.data)
                if not series_end_serializer.is_valid():
                    return Response(series_end_serializer.errors, status=400)
                data = series_end_serializer.validated_data
                match.status = MatchStatus.FINISHED
                match.save()
                redis_event = f"event.{MatchEventEnum.SERIES_END.value}"

            case MatchEventEnum.MAP_RESULT:
                map_result_serializer = MatchEventMapResultSerializer(data=request.data)
                if not map_result_serializer.is_valid():
                    return Response(map_result_serializer.errors, status=400)
                data = map_result_serializer.validated_data
                redis_event = f"event.{MatchEventEnum.MAP_RESULT.value}"
            case MatchEventEnum.SIDE_PICKED:
                redis_event = f"event.{MatchEventEnum.SIDE_PICKED.value}"
            case MatchEventEnum.MAP_PICKED:
                redis_event = f"event.{MatchEventEnum.MAP_PICKED.value}"
            case MatchEventEnum.MAP_VETOED:
                redis_event = f"event.{MatchEventEnum.MAP_VETOED.value}"
            case MatchEventEnum.ROUND_END:
                data = request.data
                redis_event = f"event.{MatchEventEnum.ROUND_END.value}"
            case MatchEventEnum.GOING_LIVE:
                going_live_serializer = MatchEventGoingLiveSerializer(data=request.data)
                if not going_live_serializer.is_valid():
                    return Response(going_live_serializer.errors, status=400)
                data = going_live_serializer.validated_data
                match.status = MatchStatus.LIVE
                match.save()
                redis_event = f"event.{MatchEventEnum.GOING_LIVE.value}"

        self.publish_event(redis_event, data)
        print(f"Published event: {redis_event} with data: {data}")
        return Response({"event": redis_event, "data": data}, status=200)

    @action(detail=True, methods=["POST"])
    def map_ban(self, request, pk):
        try:
            match = Match.objects.get(id=pk)
        except Match.DoesNotExist:
            return Response({"message": f"Match with id {pk} not exists"}, status=400)
        match_map_ban_serializer = MatchBanMapSerializer(data=request.data)
        if not match_map_ban_serializer.is_valid():
            return Response(match_map_ban_serializer.errors, status=400)
        team_id = match_map_ban_serializer.validated_data.get("team_id")
        map_tag = match_map_ban_serializer.validated_data.get("map_tag")
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            return Response(
                {"message": f"Team with id {team_id} not exists"}, status=400
            )
        try:
            map = Map.objects.get(tag=map_tag)
        except Map.DoesNotExist:
            return Response(
                {"message": f"Map with tag {map_tag} not exists"}, status=400
            )
        if match.team1 != team and match.team2 != team:
            return Response(
                {"message": f"Team {team.name} is not part of match {match.id}"},
                status=400,
            )
        if match.map_bans.filter(map=map).exists():
            return Response(
                {"message": f"Map {map_tag} already banned by team {team.name}"},
                status=400,
            )
        if match.map_bans.filter().last() == team:
            return Response(
                {
                    "message": f"Team {team.name} already banned a map. Wait for the other team to ban a map."
                },
                status=400,
            )
        # if match.map_bans.count() == 0 and team == match.team2:
        #     return Response(
        #         {
        #             "message": f"Team {team.name} is not allowed to ban a map. Team 1 has to ban first"
        #         },
        #         status=400,
        #     )
        if match.maps.count() == 1:
            return Response(
                {"message": "Only one map left. You can't ban more maps"}, status=400
            )
        if match.type == MatchType.BO3 and match.maps.count() == 3:
            return Response({"message": "Both teams already banned 3 maps"}, status=400)
        if match.map_picks.filter(map=map).exists():
            return Response(
                {"message": f"Map {map_tag} cannot be banned. It was already picked"},
                status=400,
            )
        match_map_ban = MatchMapBan.objects.create(team=team, map=map)
        match.map_bans.add(match_map_ban)
        match.maps.remove(map)
        match.save()
        current_match = cache.get("current_match")
        if not current_match:
            return Response({"message": "No current match in cache"}, status=400)
        current_match = json.loads(current_match)
        current_match["maplist"].remove(map.tag)
        cache.set("current_match", json.dumps(current_match), timeout=60 * 60 * 24 * 7)
        return Response(match_map_ban_serializer.data, status=201)

    @action(detail=True, methods=["POST"])
    def map_pick(self, request, pk):
        try:
            match = Match.objects.get(id=pk)
        except Match.DoesNotExist:
            return Response({"message": f"Match with id {pk} not exists"}, status=400)
        match_map_pick_serializer = MatchPickMapSerializer(data=request.data)
        if not match_map_pick_serializer.is_valid():
            return Response(match_map_pick_serializer.errors, status=400)
        team_id = match_map_pick_serializer.validated_data.get("team_id")
        map_tag = match_map_pick_serializer.validated_data.get("map_tag")
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            return Response(
                {"message": f"Team with id {team_id} not exists"}, status=400
            )
        try:
            map = Map.objects.get(tag=map_tag)
        except Map.DoesNotExist:
            return Response(
                {"message": f"Map with tag {map_tag} not exists"}, status=400
            )
        if match.team1 != team and match.team2 != team:
            return Response(
                {"message": f"Team {team.name} is not part of match {match.id}"},
                status=400,
            )
        if match.map_picks.filter(map=map).exists():
            return Response(
                {"message": f"Map {map_tag} already picked by team"},
                status=400,
            )
        # if match.map_picks.count() == 0 and team == match.team2:
        #     return Response(
        #         {
        #             "message": f"Team {team.name} is not allowed to pick a map. Team 1 has to pick first"
        #         },
        #         status=400,
        #     )
        if match.map_picks.count() == 2:
            return Response({"message": "Both teams already picked a map"}, status=400)
        if not match.maps.filter(tag=map_tag).exists():
            return Response(
                {"message": f"Map {map_tag} is not available to be picked"},
                status=400,
            )

        map_selected = MatchMapSelected.objects.create(team=team, map=map)
        match.map_picks.add(map_selected)
        match.save()
        current_match = cache.get("current_match")
        if not current_match:
            return Response({"message": "No current match in cache"}, status=400)

        current_match = json.loads(current_match)

        map_index = current_match["maplist"].index(map.tag)
        current_match["maplist"].pop(map_index)
        # add map to firts position if is the first pick, else add to second position

        if match.map_picks.count() == 1:
            current_match["maplist"].insert(0, map.tag)
        else:
            current_match["maplist"].insert(1, map.tag)
        cache.set("current_match", json.dumps(current_match), timeout=60 * 60 * 24 * 7)
        return Response(match_map_pick_serializer.data, status=201)

    @action(detail=True, methods=["POST"])
    def recreate(self, request, pk):
        try:
            match = Match.objects.get(id=pk)
        except Match.DoesNotExist:
            return Response({"message": f"Match with id {pk} not exists"}, status=400)
        new_match = Match.objects.create(
            type=match.type,
            team1=match.team1,
            team2=match.team2,
        )
        new_match.maps.set(Map.objects.all())
        new_match.save()
        new_match_serializer = MatchSerializer(new_match)
        if not new_match_serializer:
            return Response({"message": "Error recreating match"}, status=400)
        current_match = cache.get("current_match")
        if not current_match:
            return Response({"message": "No current match in cache"}, status=400)
        current_match = json.loads(current_match)
        current_match["matchid"] = new_match.id
        current_match["maplist"] = [map.tag for map in Map.objects.all()]
        cache.set("current_match", json.dumps(current_match), timeout=60 * 60 * 24 * 7)
        return Response(new_match_serializer.data, status=201)

    @action(detail=True, methods=["POST"])
    def shuffle_teams(self, request, pk):
        try:
            match = Match.objects.get(id=pk)
        except Match.DoesNotExist:
            return Response({"message": f"Match with id {pk} not exists"}, status=400)

        players = match.team1.players.all() | match.team2.players.all()
        players = list(players)
        team1, team2 = self.__divide_players(players)
        match.team1.players.set(team1)
        match.team2.players.set(team2)
        match.save()
        match_serializer = MatchSerializer(match)
        if not match_serializer:
            return Response({"message": "Error shuffling teams"}, status=400)

        return Response(match_serializer.data, status=201)


class MapViewSet(viewsets.ModelViewSet):
    queryset = Map.objects.all()
    serializer_class = MapSerializer
