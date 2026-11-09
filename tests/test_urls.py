import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_root_renders_home(client):
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert "Sky Habit" in response.content.decode()
