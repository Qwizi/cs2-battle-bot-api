import pytest
from rest_framework import status

from cs2_battle_bot.tests.conftest import api_client, client_with_api_key
from players.models import Player

API_ENDPOINT = "/api/players/"

@pytest.mark.django_db
@pytest.mark.parametrize("methods", ["get", "post", "put", "patch", "delete"])
def test_players_unauthorized(methods, api_client, player):

    if methods == "get":
        response = api_client.get(API_ENDPOINT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response2 = api_client.get(f"{API_ENDPOINT}{player.id}/")
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED
    elif methods == "post":
        response = api_client.post(API_ENDPOINT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    elif methods == "put":
        response = api_client.put(f"{API_ENDPOINT}{player.id}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    elif methods == "patch":
        response = api_client.patch(f"{API_ENDPOINT}{player.id}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    elif methods == "delete":
        response = api_client.delete(f"{API_ENDPOINT}{player.id}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_players_empty_list(client_with_api_key):
    response = client_with_api_key.get(API_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 0
    assert response.data["results"] == []
    assert response.data["next"] is None
    assert response.data["previous"] is None


@pytest.mark.django_db
def test_get_players_list(client_with_api_key, player):
    response = client_with_api_key.get(API_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["discord_user"] is not None
    assert response.data["results"][0]["steam_user"] is not None
    assert response.data["next"] is None
    assert response.data["previous"] is None

@pytest.mark.django_db
def test_get_player(client_with_api_key, player):
    response = client_with_api_key.get(f"{API_ENDPOINT}{player.id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["discord_user"] is not None
    assert response.data["steam_user"] is not None


@pytest.mark.django_db
@pytest.mark.skip
def test_create_player(client_with_api_key):
    pass

@pytest.mark.django_db
def test_delete_player(client_with_api_key, player):
    response = client_with_api_key.delete(f"{API_ENDPOINT}{player.id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Player.objects.count() == 0