import pytest

from data_utils import MissingEnvironmentVariableError, require_env, require_envs


def test_require_env_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "secret")

    assert require_env("GEMINI_API_KEY") == "secret"


def test_require_env_treats_empty_string_as_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")

    with pytest.raises(MissingEnvironmentVariableError):
        require_env("GEMINI_API_KEY")


def test_require_envs_reports_every_missing_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRESENT", "1")
    monkeypatch.delenv("ABSENT_ONE", raising=False)
    monkeypatch.delenv("ABSENT_TWO", raising=False)

    with pytest.raises(MissingEnvironmentVariableError) as excinfo:
        require_envs(["PRESENT", "ABSENT_ONE", "ABSENT_TWO"])

    assert excinfo.value.names == ["ABSENT_ONE", "ABSENT_TWO"]
