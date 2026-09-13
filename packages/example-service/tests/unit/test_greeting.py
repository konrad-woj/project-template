from fastapi.testclient import TestClient

from example_service.main import app

client = TestClient(app)


def test_get_greeting_returns_message() -> None:
    response = client.get("/greetings/World")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_get_greeting_rejects_name_over_max_length() -> None:
    response = client.get(f"/greetings/{'a' * 101}")

    assert response.status_code == 422
    assert "exceeds the maximum length" in response.json()["detail"]
