import pytest


@pytest.fixture(autouse=True)
def set_gemini_api_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-for-unit-tests")
