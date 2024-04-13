import pytest

from guilds.models import Guild
from players.models import DiscordUser


@pytest.mark.django_db
def test_create_guild(guild_data):
    guild = Guild.objects.create_guild(**guild_data)
    assert guild.name == guild_data["name"]
    assert guild.owner.username == guild_data["owner_username"]
    assert guild.guild_id == guild_data["guild_id"]
    # +1 because the owner is also a member
    assert guild.members.count() == len(guild_data["members"]) + 1

    assert DiscordUser.objects.filter(user_id=guild_data["owner_id"]).exists() is True
    assert guild.members.filter(user_id=guild_data["owner_id"]).exists() is True
    assert DiscordUser.objects.count() == len(guild_data["members"]) + 1
