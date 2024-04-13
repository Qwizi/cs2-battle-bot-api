import pytest

from players.models import DiscordUser, SteamUser, Player


@pytest.fixture
def discord_user_data():
    return {
        "user_id": "1133332759834787860",
        "username": "qwizi2",
    }


@pytest.fixture
def steam_user_data():
    return {
        "username": "Qwizi",
        "steamid64": "76561198190469450",
        "steamid32": "STEAM_1:0:115101861",
        "profile_url": "https://steamcommunity.com/id/34534645645/",
        "avatar": "https://avatars.steamstatic.com/d95f7e69a5cfb9c09acf1ecb6a2106239297f668_full.jpg",
    }

@pytest.fixture
def player(discord_user_data, steam_user_data):
    discord_user = DiscordUser.objects.create(**discord_user_data)
    steam_user = SteamUser.objects.create(**steam_user_data)
    return Player.objects.create(discord_user=discord_user, steam_user=steam_user)