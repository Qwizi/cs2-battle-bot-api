import pytest
from django.conf import settings
from django.test import RequestFactory
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse_lazy

from matches.models import Match, MatchStatus, MatchType, MatchConfig, GameMode
from matches.tests.conftest import configs
from servers.tests.conftest import server
from players.tests.conftest import teams_with_players, default_author
@pytest.mark.django_db
@pytest.mark.parametrize("with_server", [True, False])
@pytest.mark.parametrize("config", configs)
def test_match_model(with_server, server, config, guild, default_author):
    server = server if with_server else None
    factory = RequestFactory()

    # Create a request
    request = factory.get('/')
    match_config = MatchConfig.objects.get(name=config)
    new_match: Match = Match.objects.create(
        config=match_config,
        author=default_author.player.discord_user,
        guild=guild,
        server=server
    )
    new_match.create_webhook_cvars(str(reverse_lazy("match-webhook", args=[new_match.pk], request=request)))
    assert new_match.status == MatchStatus.CREATED

    assert new_match.config.name == match_config.name
    assert new_match.config.game_mode == match_config.game_mode
    assert new_match.config.type == match_config.type
    assert new_match.config.clinch_series == match_config.clinch_series
    assert new_match.config.max_players == match_config.max_players
    assert new_match.config.map_pool == match_config.map_pool
    assert new_match.config.map_sides == match_config.map_sides

    assert new_match.team1 is not None
    assert new_match.team2 is not None
    assert new_match.team1.name == "Team 1"
    assert new_match.team2.name == "Team 2"
    assert new_match.winner_team is None
    assert new_match.map_bans.count() == 0
    assert new_match.map_picks.count() == 0
    assert new_match.last_map_ban is None
    assert new_match.last_map_pick is None
    assert new_match.maplist is None
    assert new_match.server == server
    assert new_match.guild == guild
    assert new_match.author == default_author.player.discord_user
    assert new_match.message_id is None
    assert new_match.embed is not None

    team1_players_dict = new_match.get_team1_players_dict()
    team2_players_dict = new_match.get_team2_players_dict()

    assert team1_players_dict["name"] == "Team 1"
    assert team2_players_dict["name"] == "Team 2"

    assert len(team1_players_dict["players"]) == 1
    assert len(team2_players_dict["players"]) == 0

    assert new_match.api_key_header == "Authorization"
    assert new_match.load_match_command_name == "matchzy_loadmatch_url"
    assert new_match.get_author_token() == Token.objects.get(user=default_author).key
    assert new_match.get_connect_command() == "" if with_server is False else server.get_connect_string()

    matchzy_config = new_match.get_matchzy_config()
    assert matchzy_config["matchid"] == new_match.pk
    assert matchzy_config["team1"] == team1_players_dict
    assert matchzy_config["team2"] == team2_players_dict
    assert matchzy_config["num_maps"] == 1 if match_config.type == MatchType.BO1 else 3
    assert matchzy_config["maplist"] == new_match.maplist
    assert matchzy_config["map_sides"] == match_config.map_sides
    assert matchzy_config["clinch_series"] == match_config.clinch_series
    assert matchzy_config["players_per_team"] == 1
    assert matchzy_config["cvars"] == new_match.cvars
    assert matchzy_config["cvars"]["matchzy_remote_log_url"] == reverse_lazy("match-webhook", args=[new_match.pk], request=request)
    assert matchzy_config["cvars"]["matchzy_remote_log_header_key"] == new_match.api_key_header
    assert matchzy_config["cvars"]["matchzy_remote_log_header_value"] == f"Bearer {new_match.get_author_token()}"

    if match_config.game_mode == GameMode.WINGMAN:
        assert matchzy_config["wingman"] is True

    assert new_match.api_key_header == "Authorization"
    assert new_match.load_match_command_name == "matchzy_loadmatch_url"

@pytest.mark.django_db
@pytest.mark.parametrize("config", configs)
def test_match_get_team1_players_dict(match, config):
    match.config = MatchConfig.objects.get(name=config)
    match.save()
    team1_dict = match.get_team1_players_dict()
    assert team1_dict["name"] == match.team1.name
    assert len(team1_dict["players"]) == match.team1.players.count()
    assert len(team1_dict["players"]) == 1

@pytest.mark.django_db
@pytest.mark.parametrize("config", configs)
def test_match_get_team2_players_dict(match, config):
    match.config = MatchConfig.objects.get(name=config)
    match.save()
    team2_dict = match.get_team2_players_dict()
    assert team2_dict["name"] == match.team2.name
    assert len(team2_dict["players"]) == match.team2.players.count()
    assert len(team2_dict["players"]) == 0

@pytest.mark.django_db
@pytest.mark.parametrize("config", configs)
def test_match_get_matchzy_config(rf, match, config):
    request = rf.get("/")
    match.config = MatchConfig.objects.get(name=config)
    match.save()
    matchzy_config = match.get_matchzy_config()
    assert matchzy_config["matchid"] == match.pk
    assert matchzy_config["team1"] == match.get_team1_players_dict()
    assert matchzy_config["team2"] == match.get_team2_players_dict()
    assert matchzy_config["num_maps"] == 1 if match.config.type == MatchType.BO1 else 3
    assert matchzy_config["maplist"] == match.maplist
    assert matchzy_config["map_sides"] == match.config.map_sides
    assert matchzy_config["clinch_series"] == match.config.clinch_series
    assert matchzy_config["players_per_team"] == 1
    assert matchzy_config["cvars"] == match.cvars
    assert matchzy_config["cvars"]["matchzy_remote_log_url"] == reverse_lazy("match-webhook", args=[match.pk], request=request)
    assert matchzy_config["cvars"]["matchzy_remote_log_header_key"] == match.api_key_header
    assert matchzy_config["cvars"]["matchzy_remote_log_header_value"] == f"Bearer {match.get_author_token()}"

    if match.config.game_mode == GameMode.WINGMAN:
        assert matchzy_config["wingman"] is True


@pytest.mark.django_db
@pytest.mark.parametrize("config", configs)
def test_get_connect_command(match, server, config):
    match.server = server
    match.save()
    assert match.get_connect_command() == server.get_connect_string()
