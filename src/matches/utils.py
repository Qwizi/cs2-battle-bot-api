import json
import math
from time import sleep
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rcon import Client, EmptyResponse, SessionTimeout, WrongPassword
import redis
from rest_framework.authtoken.models import Token

from guilds.models import Guild
from matches.models import (
    Map,
    Match,
    MapBan,
    MapPick,
    MatchStatus,
    MatchType,
)
from matches.serializers import (
    CreateMatchSerializer,
    MatchBanMapSerializer,
    MatchEventEnum,
    MatchEventGoingLiveSerializer,
    MatchEventMapResultSerializer,
    MatchEventSerializer,
    MatchEventSeriesEndSerializer,
    MatchEventSeriesStartSerializer,
    MatchPickMapSerializer,
    MatchPlayerJoin,
    MatchSerializer, MatchBanMapResultSerializer, MatchPickMapResultSerializer,
)
from players.models import DiscordUser, Player, Team
from players.utils import create_default_teams, divide_players
from rest_framework.request import Request
from rest_framework.response import Response

from servers.models import Server
from steam import game_servers as gs

UserModel = get_user_model()


def send_rcon_command(host: str, port: str, rcon_password: str, command: str, *args):
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
                host,
                int(port),
                passwd=rcon_password,
        ) as client:
            return client.run(command, *args)
    except (EmptyResponse, SessionTimeout, WrongPassword) as e:
        print(f"Error sending RCON command: {e}")
        return None


def check_server_is_available_for_match(server: Server) -> bool:
    """
    Check if the server is available for a match.

    Args:
    -----
        server (Server): Server object.

    Returns:
    --------
        bool: True if the server is available, False otherwise.
    """
    if Match.objects.filter(server=server, status=MatchStatus.LIVE).exists() or Match.objects.filter(server=server, status=MatchStatus.STARTED).exists():
        return False
    return True


def create_match(request: Request) -> Response:
    """
    Create a new match.

    Args:
    -----
        request (Request): Request object.

    Returns:
    --------
        Response: Response object.
    """
    serializer = CreateMatchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    discord_users_ids = serializer.validated_data.get("discord_users_ids")
    match_type = serializer.validated_data.get("match_type", "BO1")
    clinch_series = serializer.validated_data.get("clinch_series", False)
    map_sides = serializer.validated_data.get(
        "map_sides", ["knife", "team1_ct", "team2_ct"]
    )
    discord_users_ids = list(set(discord_users_ids))
    author_id = serializer.validated_data.get("author_id")
    server_id = serializer.validated_data.get("server_id")
    guild_id = serializer.validated_data.get("guild_id")
    cvars = serializer.validated_data.get("cvars")
    if len(discord_users_ids) < 2:
        return Response({"message": "At least 2 players are required"}, status=400)
    server = None
    if server_id:
        server = get_object_or_404(Server, pk=server_id)
        if not server.check_online():
            return Response(
                {"message": "Server is not online. Cannot create match"}, status=400
            )
        if not Match.objects.check_server_is_available_for_match(server):
            return Response(
                {"message": "Server is not available for a match. Another match is already running"},
                status=400,
            )
    discord_users_list: list[DiscordUser] = []
    discord_users_not_found: list[str] = []
    for discord_user_id in discord_users_ids:
        try:
            discord_user = DiscordUser.objects.get(user_id=discord_user_id)
            discord_users_list.append(discord_user)
        except DiscordUser.DoesNotExist as e:
            discord_users_not_found.append(discord_user_id)
    if discord_users_not_found:
        return Response(
            {
                "message": f"Discord users not found",
                "users": discord_users_not_found,
            },
            status=404,
        )
    try:
        author = DiscordUser.objects.get(user_id=author_id)
    except DiscordUser.DoesNotExist as e:
        return Response(
            {
                "message": "Author not found",
                "user_id": author_id,
            },
            status=404,
        )

    players_list: list[Player] = []
    for discord_user in discord_users_list:
        player: Player = get_object_or_404(Player, discord_user=discord_user)
        if player.steam_user is None:
            return Response(
                {
                        "message": f"Discord user {discord_user.username} has no connected player",
                        "user_id": discord_user.user_id,
                },
                    status=404,
            )
        players_list.append(player)

    team1, team2 = create_default_teams("Team 1", "Team 2", players_list)
    guild = get_object_or_404(Guild, pk=guild_id)
    new_match = Match.objects.create_match(
        team1=team1,
        team2=team2,
        author=author,
        type=match_type,
        clinch_series=clinch_series,
        map_sides=map_sides,
        server=server,
        cvars=cvars,
        guild=guild
    )
    new_match_serializer = MatchSerializer(new_match)
    return Response(new_match_serializer.data, status=200)


def load_match(pk: int) -> Response:
    """
    Load a match into the server.

    Args:
    -----
        pk (int): Match ID.

    Returns:
    --------
        Response: Response object.
    """
    match = get_object_or_404(Match, pk=pk)
    if not match.server:
        return Response(
            {"message": "Match has no server assigned. Cannot load match"}, status=400
        )
    # return f"matchzy_loadmatch_url {match_url} {api_key_header} {api_key}"
    load_match_command_split = match.get_load_match_command().split(" ")
    load_match_command = load_match_command_split[0]
    match_url = load_match_command_split[1]
    api_key_header = load_match_command_split[2]
    api_key = load_match_command_split[3]

    send_rcon_command(match.server.ip, match.server.port, match.server.rcon_password, "css_endmatch")
    sleep(5)
    match_serializer = MatchSerializer(match)
    send_rcon_command(match.server.ip, match.server.port, match.server.rcon_password, load_match_command, match_url,
                      api_key_header, api_key)
    return Response(match_serializer.data, status=200)


def ban_map(request: Request, pk: int) -> Response:
    """
    Ban a map from the match.

    Args:
    -----
        request (Request): Request object.
        pk (int): Match ID.

    Returns:
    --------
        Response: Response object.
    """
    match: Match = get_object_or_404(Match, pk=pk)
    match_map_ban_serializer = MatchBanMapSerializer(data=request.data)
    match_map_ban_serializer.is_valid(raise_exception=True)
    interaction_user_id = match_map_ban_serializer.validated_data.get("interaction_user_id")
    try:
        player = Player.objects.get(discord_user__user_id=interaction_user_id)
    except Player.DoesNotExist as e:
        return Response({"message": e.args}, status=404)
    try:
        user_team = Team.objects.get(players__discord_user__user_id=interaction_user_id)
    except Team.DoesNotExist as e:
        return Response({"message": e.args}, status=404)
    if not user_team != match.team1 and not user_team != match.team2:
        return Response(
            {"message": f"User {player.discord_user.username} is not part of match {match.id}"},
            status=400,
        )
    map_tag = match_map_ban_serializer.validated_data.get("map_tag")
    map = get_object_or_404(Map, tag=map_tag)
    if player.pk != user_team.leader.pk:
        print(player.discord_user.username)
        print(user_team.leader.discord_user.username)
        return Response(
            {"message": f"User {player.discord_user.username} is not the leader of team {user_team.name}"},
            status=400,
        )
    if match.map_bans.filter(map=map).exists():
        return Response(
            {"message": f"Map {map_tag} already banned"},
            status=400,
        )
    last_match_map_ban = match.map_bans.all().order_by("-created_at").first()
    map_bans_count = match.map_bans.count()
    if map_bans_count > 0 and last_match_map_ban.team == user_team:
        return Response(
            {
                "message": f"Team {user_team.name} already banned a map. Wait for the other team to ban a map."
            },
            status=400,
        )
    if map_bans_count == 0 and user_team == match.team2:
        return Response(
            {
                "message": f"Team {user_team.name} is not allowed to ban a map. Team 1 has to ban first"
            },
            status=400,
        )
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

    if (
            map_bans_count == 2
            and match.type == MatchType.BO3
            and match.map_picks.count() < 2
    ):
        return Response(
            {
                "message": "Both teams already banned 2 maps. Wait for both teams to pick a map"
            },
            status=400,
        )
    match.ban_map(user_team, map)
    ban_result_serializer = MatchBanMapResultSerializer(
        data={
            "banned_map": map.tag,
            "next_ban_team_leader": match.team1.leader.discord_user.username
            if match.team2 == user_team
            else match.team2.leader.discord_user.username,
            "maps_left": match.maplist,
            "map_bans_count": match.map_bans.count(),
        }
    )
    ban_result_serializer.is_valid(raise_exception=True)
    return Response(ban_result_serializer.data, status=200)


def pick_map(request: Request, pk: int) -> Response["MatchPickMapResultSerializer"]:
    """
    Pick a map for the match.

    Args:
    -----
        request (Request): Request object.
        pk (int): Match ID.


    Returns:
    --------
        Response: Response object.
    """
    match: Match = get_object_or_404(Match, pk=pk)
    match_map_pick_serializer = MatchPickMapSerializer(data=request.data)
    match_map_pick_serializer.is_valid(raise_exception=True)
    interaction_user_id = match_map_pick_serializer.validated_data.get("interaction_user_id")

    if match.type == MatchType.BO1:
        return Response({"message": "Cannot pick a map in a BO1 match"}, status=400)

    try:
        player = Player.objects.get(discord_user__user_id=interaction_user_id)
    except Player.DoesNotExist as e:
        return Response({"message": e.args}, status=404)
    try:
        user_team = Team.objects.get(players__discord_user__user_id=interaction_user_id)
    except Team.DoesNotExist as e:
        return Response({"message": e.args}, status=404)

    if not user_team != match.team1 and not user_team != match.team2:
        return Response(
            {"message": f"User {player.discord_user.username} is not part of match {match.id}"},
            status=400,
        )

    map_tag = match_map_pick_serializer.validated_data.get("map_tag")
    map = get_object_or_404(Map, tag=map_tag)
    if player.pk != user_team.leader.pk:
        print(player.discord_user.username)
        print(user_team.leader.discord_user.username)
        return Response(
            {"message": f"User {player.discord_user.username} is not the leader of team {user_team.name}"},
            status=400,
        )
    if match.map_picks.filter(map=map).exists():
        return Response(
            {"message": f"Map {map_tag} already picked by team"},
            status=400,
        )
    last_pick = match.map_picks.all().order_by("-created_at").first()
    map_picks_count = match.map_picks.count()
    map_bans_count = match.map_bans.count()

    if map_bans_count < 2:
        return Response(
            {"message": "Both teams have to ban 1 map before picking a map"}, status=400
        )


    if map_picks_count > 0 and last_pick.team == user_team:
        return Response(
            {
                "message": f"Team {user_team.name} already picked a map. Wait for the other team to pick a map."
            },
            status=400,
        )
    if map_picks_count == 0 and user_team == match.team2:
        return Response(
            {
                "message": f"Team {user_team.name} is not allowed to pick a map. Team 1 has to pick first"
            },
            status=400,
        )
    if map_picks_count == 2:
        return Response({"message": "Both teams already picked a map"}, status=400)
    if not match.maps.filter(tag=map_tag).exists():
        return Response(
            {"message": f"Map {map_tag} is not available to be picked"},
            status=400,
        )

    match.pick_map(user_team, map)
    map_pick_result_serializer = MatchPickMapResultSerializer(
        data={
            "picked_map": map.tag,
            "next_pick_team_leader": match.team1.leader.discord_user.username
            if match.team2 == user_team
            else match.team2.leader.discord_user.username,
            "maps_left": match.maplist,
            "map_picks_count": match.map_picks.count(),
        }
    )
    map_pick_result_serializer.is_valid(raise_exception=True)
    return Response(map_pick_result_serializer.data, status=200)


def shuffle_teams(pk: int) -> Response:
    """
    Shuffle the teams of a match.

    Args:
    -----
        pk (int): Match ID.

    Returns:
    --------
        Response: Response object.
    """
    match: Match = get_object_or_404(Match, pk=pk)
    players = match.team1.players.all() | match.team2.players.all()
    players = list(players)
    team1, team2 = divide_players(players)
    match.team1.players.set(team1)
    match.team1.leader = team1[0]
    match.team2.players.set(team2)
    match.team2.leader = team2[0]
    match.save()
    match_serializer = MatchSerializer(match)
    if not match_serializer:
        return Response({"message": "Error shuffling teams"}, status=400)
    return Response(match_serializer.data, status=200)


def publish_event(event: str, data: dict):
    """
    Publish an event to the Redis server.

    Args:
    -----
        event (str): Event name.
        data (dict): Event data.

    Returns:
    --------
        None
    """
    redis_client = redis.StrictRedis(host="redis", port=6379, db=0)
    redis_client.publish(event, json.dumps(data))


def process_webhook(request: Request) -> Response:
    """
    Process a webhook event.

    Args:
    -----
        request (Request): Request object.

    Returns:
    --------
        Response: Response object.
    """
    match_event_serializer = MatchEventSerializer(data=request.data)
    if not match_event_serializer.is_valid():
        return Response(match_event_serializer.errors, status=400)
    match_id = match_event_serializer.validated_data.get("matchid")
    match: Match = get_object_or_404(Match, pk=match_id)
    data = None
    redis_event = None
    match match_event_serializer.validated_data.get("event"):
        case MatchEventEnum.SERIES_START:
            series_start_serializer = MatchEventSeriesStartSerializer(data=request.data)
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

    publish_event(redis_event, data)
    print(f"Published event: {redis_event} with data: {data}")
    return Response({"event": redis_event, "data": data}, status=200)


def join_match(request: Request, pk: int) -> Response:
    """
    Join a match.

    Args:
    -----
        request (Request): Request object.
        pk (int): Match ID.

    Returns:
    --------
        Response: Response object.
    """
    match: Match = get_object_or_404(Match, pk=pk)
    match_player_join_serializer = MatchPlayerJoin(data=request.data)
    if not match_player_join_serializer.is_valid():
        return Response(match_player_join_serializer.errors, status=400)

    discord_user_id = match_player_join_serializer.validated_data.get("discord_user_id")
    player = get_object_or_404(Player, discord_user__user_id=discord_user_id)
    if match.team1.players.filter(pk=player.id).exists():
        return Response(
            {"message": f"Player {player.steam_user.username} is already in team 1"},
            status=400,
        )
    if match.team2.players.filter(pk=player.id).exists():
        return Response(
            {"message": f"Player {player.steam_user.username} is already in team 2"},
            status=400,
        )
    if match.team1.players.count() < match.team2.players.count():
        match.team1.players.add(player)
    else:
        match.team2.players.add(player)
    match.save()
    match_serializer = MatchSerializer(match)
    return Response(match_serializer.data, status=200)


def recreate_match(pk: int) -> Response:
    """
    Create a new match with the same teams.

    Args:
    -----
        pk (int): Match ID.

    Returns:
    --------
        Response: Response object.
    """
    match: Match = get_object_or_404(Match, pk=pk)
    new_match = Match.objects.create(
        type=match.type,
        team1=match.team1,
        team2=match.team2,
    )
    new_match.maps.set(Map.objects.all())
    new_match.save()
    new_match_serializer = MatchSerializer(new_match)
    return Response(new_match_serializer.data, status=201)
