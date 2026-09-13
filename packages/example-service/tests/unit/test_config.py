from example_service.config import ServiceSettings, load_greeting_config


def test_service_settings_default_greeting_style() -> None:
    assert ServiceSettings().greeting_style == "default"


def test_load_greeting_config_default_defers_to_library_template() -> None:
    config = load_greeting_config("default")

    assert config.template is None
    assert config.max_name_length == 100


def test_load_greeting_config_enthusiastic_overrides_template() -> None:
    config = load_greeting_config("enthusiastic")

    assert config.template == "HELLO, {name}!!!"
