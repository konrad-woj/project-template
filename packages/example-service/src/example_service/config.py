"""Environment-driven settings and Hydra-composed domain config.

`ServiceSettings` (via `pydantic-settings`) reads deployment-level values from the environment or
`.env` — including which Hydra config variant to compose. `load_greeting_config` then composes
that variant from `conf/` and validates it into a `GreetingConfig`. This is the pattern for
combining the two: env vars select the variant, Hydra composes the structured config for it.

Example:
    settings = ServiceSettings()
    greeting_config = load_greeting_config(settings.greeting_style)
"""

from pathlib import Path

from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from omegaconf import OmegaConf
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

_CONF_DIR = Path(__file__).parent / "conf"


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EXAMPLE_SERVICE_", env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    greeting_style: str = "default"


class GreetingConfig(BaseModel):
    template: str | None
    max_name_length: int


def load_greeting_config(greeting_style: str) -> GreetingConfig:
    """Compose `conf/greeting/{greeting_style}.yaml` and validate it into a `GreetingConfig`."""
    GlobalHydra.instance().clear()
    with initialize_config_dir(config_dir=str(_CONF_DIR), version_base=None):
        composed = compose(config_name="config", overrides=[f"greeting={greeting_style}"])
    return GreetingConfig.model_validate(OmegaConf.to_object(composed.greeting))
