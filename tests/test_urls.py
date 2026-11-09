from django.urls import reverse


def test_root_redirects_to_swagger(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.url == reverse("swagger-ui")
