import pytest

from matches.models import Map, MatchType, Match
from players.tests.conftest import player, discord_user_data, steam_user_data, players, teams, teams_with_players, default_author
from servers.tests.conftest import server, server_data
from guilds.tests.conftest import guild, guild_data
@pytest.fixture
def map_data():
    return {
        "name": "Mirage",
        "tag": "de_mirage"
    }


@pytest.mark.django_db
@pytest.fixture(autouse=True)
def default_maps():
    maps_dict = [
        {
            "name": "Anubis",
            "tag": "de_anubis"
        },
        {
            "name": "Overpass",
            "tag": "de_overpass"
        },
        {
            "name": "Nuke",
            "tag": "de_nuke"
        },
        {
            "name": "Mirage",
            "tag": "de_mirage"
        },
        {
            "name": "Ancient",
            "tag": "de_ancient"
        },
        {
            "name": "Inferno",
            "tag": "de_inferno"
        },
        {
            "name": "Vertigo",
            "tag": "de_vertigo"
        }
    ]
    maps_obj = [Map.objects.get_or_create(**map) for map in maps_dict]


@pytest.fixture
def match_data(players, default_author, guild):
    return {
        "discord_users_ids": [player.discord_user.user_id for player in players],
        "author_id": default_author.player.discord_user.user_id,
        "guild_id": guild.id,
        "match_type": MatchType.BO1,
        "players_per_team": 5,
        "clinch_series": False,
        "map_sides": ["knife", "knife", "knife"],
    }


@pytest.fixture
def match(teams_with_players, players, default_author, guild):
    team1, team2 = teams_with_players
    new_match = Match.objects.create_match(
        team1=team1,
        team2=team2,
        author=default_author.player.discord_user,
        map_sides=["knife", "knife", "knife"],
        guild=guild
    )
    return new_match

@pytest.fixture
def match_with_server(server, teams_with_players, default_author, guild):
    team1, team2 = teams_with_players
    new_match = Match.objects.create_match(
        team1=team1,
        team2=team2,
        author=default_author.player.discord_user,
        map_sides=["knife", "knife", "knife"],
        server=server,
        guild=guild
    )
    return new_match