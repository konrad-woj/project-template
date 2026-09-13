"""Environment variable access with fail-fast errors at process startup.

Example:
    >>> import os
    >>> os.environ["GEMINI_API_KEY"] = "secret"
    >>> require_env("GEMINI_API_KEY")
    'secret'
"""

import os


class MissingEnvironmentVariableError(RuntimeError):
    def __init__(self, names: list[str]) -> None:
        super().__init__(f"Missing required environment variable(s): {', '.join(names)}")
        self.names = names


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingEnvironmentVariableError([name])
    return value


def require_envs(names: list[str]) -> dict[str, str]:
    """Reads every name up front so a misconfigured deployment fails on the first missing key, not the fifth.

    Example:
        >>> import os
        >>> os.environ["A"], os.environ["B"] = "1", "2"
        >>> require_envs(["A", "B"])
        {'A': '1', 'B': '2'}
    """
    values = {name: os.environ.get(name, "") for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise MissingEnvironmentVariableError(missing)
    return values
