import pytest
from rest_framework import status
from cs2_battle_bot.tests.conftest import api_client
from guilds.tests.conftest import guild_data
from cs2_battle_bot.tests.conftest import client_with_api_key
from guilds.models import Guild

API_ENDPOINT = "/api/guilds/"


@pytest.mark.django_db
@pytest.mark.parametrize("methods", ["get", "post", "put", "patch", "delete"])
def test_guilds_unauthorized(methods, api_client, guild_data):
    guild = Guild.objects.create_guild(**guild_data)

    if methods == "get":
        response = api_client.get(API_ENDPOINT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response2 = api_client.get(f"{API_ENDPOINT}{guild.id}/")
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED
    elif methods == "post":
        response = api_client.post(API_ENDPOINT)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    elif methods == "put":
        response = api_client.put(f"{API_ENDPOINT}{guild.id}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    elif methods == "patch":
        response = api_client.patch(f"{API_ENDPOINT}{guild.id}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    elif methods == "delete":
        response = api_client.delete(f"{API_ENDPOINT}{guild.id}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_get_guilds_empty_list(client_with_api_key):
    response = client_with_api_key.get(API_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 0
    assert response.data["results"] == []
    assert response.data["next"] is None
    assert response.data["previous"] is None


@pytest.mark.django_db
def test_get_guilds_list(client_with_api_key, guild_data):
    guild = Guild.objects.create_guild(**guild_data)
    response = client_with_api_key.get(API_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["name"] == guild_data["name"]
    assert response.data["results"][0]["owner"] is not None
    assert response.data["results"][0]["guild_id"] == guild_data["guild_id"]
    assert len(response.data["results"][0]["members"]) == len(guild_data["members"]) + 1
    assert response.data["next"] is None
    assert response.data["previous"] is None


@pytest.mark.django_db
def test_get_guild(client_with_api_key, guild_data):
    guild = Guild.objects.create_guild(**guild_data)
    response = client_with_api_key.get(f"{API_ENDPOINT}{guild.guild_id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == guild_data["name"]
    assert response.data["owner"] is not None
    assert response.data["guild_id"] == guild_data["guild_id"]
    assert len(response.data["members"]) == len(guild_data["members"]) + 1


@pytest.mark.django_db
def test_create_guild(client_with_api_key, guild_data):
    response = client_with_api_key.post(API_ENDPOINT, guild_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == guild_data["name"]
    assert response.data["owner"] is not None
    assert response.data["guild_id"] == guild_data["guild_id"]
    assert len(response.data["members"]) == len(guild_data["members"]) + 1

@pytest.mark.django_db
def test_delete_guild(client_with_api_key, guild_data):
    guild = Guild.objects.create_guild(**guild_data)
    response = client_with_api_key.delete(f"{API_ENDPOINT}{guild.guild_id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Guild.objects.count() == 0