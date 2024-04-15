import pytest
from rest_framework import status

from cs2_battle_bot.tests.conftest import api_client, client_with_api_key
from matches.models import Match

API_ENDPOINT = '/api/matches/'

@pytest.mark.django_db
@pytest.mark.parametrize("methods", ["get", "post", "put", "delete"])
@pytest.mark.parametrize("actions", ["load", "webhook", "ban", "pick", "recreate", "shuffle", "config", "join"])
def test_match_unauthorized(api_client, client_with_api_key, methods, actions, match):
    if methods == "get":
        response = api_client.get(API_ENDPOINT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        if actions == "config":
            response = api_client.get(f"{API_ENDPOINT}{match.pk}/config/")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            response = client_with_api_key.get(f"{API_ENDPOINT}{match.pk}/config/")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    elif methods == "post":
        response = api_client.post(API_ENDPOINT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        if actions == "load":
            response = api_client.post(f"{API_ENDPOINT}{match.pk}/load/")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        elif actions == "webhook":
            response = api_client.post(f"{API_ENDPOINT}webhook/")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        elif actions == "ban":
            response = api_client.post(f"{API_ENDPOINT}{match.pk}/ban/")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        elif actions == "pick":
            response = api_client.post(f"{API_ENDPOINT}{match.pk}/pick/")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        elif actions == "recreate":
            response = api_client.post(f"{API_ENDPOINT}{match.pk}/recreate/")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        elif actions == "shuffle":
            response = api_client.post(f"{API_ENDPOINT}{match.pk}/shuffle/")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        elif actions == "join":
            response = api_client.post(f"{API_ENDPOINT}{match.pk}/join/")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    elif methods == "put":
        response = api_client.put(f"{API_ENDPOINT}{match.pk}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    elif methods == "delete":
        response = api_client.delete(f"{API_ENDPOINT}{match.pk}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_matches_list(client_with_api_key, match, match_with_server):
    response = client_with_api_key.get(API_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == Match.objects.count()
    assert response.data["results"][0]["id"] == match.pk
    assert response.data["results"][0]["status"] == match.status
    assert response.data["results"][0]["type"] == match.type
    assert response.data["results"][0]["author"] == match.author.pk
    assert response.data["results"][0]["team1"]["id"] == match.team1.pk
    assert response.data["results"][0]["team2"]["name"] == match.team2.name
    assert response.data["results"][0]["team2"]["id"] == match.team2.pk
    assert response.data["results"][0]["team2"]["name"] == match.team2.name
    assert response.data["results"][0]["players_per_team"] == match.players_per_team
    assert response.data["results"][0]["clinch_series"] == match.clinch_series
    assert response.data["results"][0]["map_sides"] == match.map_sides
    assert response.data["results"][0]["created_at"] is not None
    assert response.data["results"][0]["updated_at"] is not None

    assert response.data["results"][1]["id"] == match_with_server.pk
    assert response.data["results"][1]["server"]["id"] == match_with_server.server.pk
    assert "rcon_password" not in response.data["results"][1]["server"]
    assert response.data["next"] is None
    assert response.data["previous"] is None


@pytest.mark.django_db
@pytest.mark.parametrize("with_server", [True, False])
def test_get_match(client_with_api_key, match, match_with_server, with_server):
    match_to_test = match if not with_server else match_with_server
    response = client_with_api_key.get(f"{API_ENDPOINT}{match_to_test.pk}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == match_to_test.pk
    assert response.data["status"] == match_to_test.status
    assert response.data["type"] == match_to_test.type
    assert response.data["author"] == match_to_test.author.pk
    assert response.data["team1"]["id"] == match_to_test.team1.pk
    assert response.data["team2"]["name"] == match_to_test.team2.name
    assert response.data["team2"]["id"] == match_to_test.team2.pk
    assert response.data["players_per_team"] == match_to_test.players_per_team
    assert response.data["clinch_series"] == match_to_test.clinch_series
    assert response.data["map_sides"] == match_to_test.map_sides
    assert response.data["cvars"] is not None
    assert response.data["created_at"] is not None
    assert response.data["updated_at"] is not None
    assert response.data["connect_command"] == ("" if not with_server else match_with_server.server.get_connect_string())
    assert response.data["load_match_command"] == match_to_test.get_load_match_command()
    assert response.data["map_bans"] == []
    assert response.data["map_picks"] == []
    if with_server:
        assert response.data["server"]["id"] == match_with_server.server.pk
        assert "rcon_password" not in response.data["server"]

    assert response.data["maplist"] == match_to_test.maplist
    assert response.data["maps"] != []