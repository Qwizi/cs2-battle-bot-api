import pytest


@pytest.fixture
def server_data():
    return {
        "ip": "127.0.0.1",
        "name": "Test Server",
        "port": 27015,
        "password": "changeme",
        "rcon_password": "changeme",
        "is_public": True,
    }
