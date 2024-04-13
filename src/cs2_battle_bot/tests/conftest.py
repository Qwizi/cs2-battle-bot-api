import pytest
from rest_framework_api_key.models import APIKey
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def client_with_api_key():
    client = APIClient()
    api_key, key = APIKey.objects.create_key(name="test")
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + key)
    client.defaults["Authorization"] = f"Bearer {key}"
    return client
