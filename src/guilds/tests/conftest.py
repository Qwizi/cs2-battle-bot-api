import pytest

from guilds.models import Guild


@pytest.fixture
def guild_data():
    return {
        "name": "Qwizi DEV",
        "guild_id": "583717343255986178",
        "owner_id": "264857503974555649",
        "owner_username": "qwizi",
        "members": [
            {"username": "qwizi2", "user_id": "1133332759834787860"},
        ]
    }


@pytest.fixture
def guild(guild_data):
    return Guild.objects.create_guild(**guild_data)