import pytest
from django.conf import settings
from django.test import RequestFactory
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse_lazy

from matches.models import Match, MatchStatus, MatchType
from servers.tests.conftest import server
from players.tests.conftest import teams_with_players, default_author
@pytest.mark.django_db
@pytest.mark.parametrize("with_server", [True, False])
@pytest.mark.parametrize("match_type", [MatchType.BO1, MatchType.BO3])
@pytest.mark.parametrize("clinch_series", [True, False])
def test_match_model(teams_with_players, default_author, with_server, match_type, server, clinch_series):
    team1, team2 = teams_with_players
    server = server if with_server else None
    factory = RequestFactory()

    # Create a request
    request = factory.get('/')
    new_match: Match = Match.objects.create_match(
        team1=team1,
        team2=team2,
        author=default_author.player.discord_user,
        type=match_type,
        clinch_series=clinch_series,
        map_sides=["knife", "knife", "knife"],
        server=server,
    )
    new_match.create_webhook_cvars(str(reverse_lazy("match-webhook", args=[new_match.pk], request=request)))
    assert new_match.status == MatchStatus.CREATED
    assert new_match.type == match_type
    assert new_match.team1 == team1
    assert new_match.team2 == team2
    assert new_match.author == default_author.player.discord_user
    assert new_match.players_per_team == 5
    assert new_match.clinch_series is clinch_series
    assert new_match.map_sides == ["knife", "knife", "knife"]
    assert new_match.maplist == new_match.maplist

    team1_players_dict = new_match.get_team1_players_dict()
    team2_players_dict = new_match.get_team2_players_dict()

    assert team1_players_dict["name"] == team1.name
    assert team2_players_dict["name"] == team2.name

    assert len(team1_players_dict["players"]) == 5
    assert len(team2_players_dict["players"]) == 5

    match_config = new_match.get_config()

    assert match_config["matchid"] == new_match.pk
    assert match_config["team1"] == team1_players_dict
    assert match_config["team2"] == team2_players_dict
    assert match_config["num_maps"] == 1 if match_type == MatchType.BO1 else 3
    assert match_config["maplist"] == new_match.maplist
    assert match_config["map_sides"] == ["knife", "knife", "knife"]
    assert match_config["clinch_series"] is clinch_series
    assert match_config["players_per_team"] == 5
    assert match_config["cvars"] == new_match.cvars
    assert match_config["cvars"]["matchzy_remote_log_url"] == reverse_lazy("match-webhook", args=[new_match.pk], request=request)
    assert match_config["cvars"]["matchzy_remote_log_header_key"] == new_match.api_key_header
    assert match_config["cvars"]["matchzy_remote_log_header_value"] == f"Bearer {new_match.get_author_token()}"

    connect_command = new_match.get_connect_command()
    assert connect_command == "" if with_server is False else server.get_connect_string()

    author_token = new_match.get_author_token()
    assert author_token == Token.objects.get(user=default_author).key

    assert new_match.load_match_command_name == "matchzy_loadmatch_url"
    assert new_match.api_key_header == "Authorization"




