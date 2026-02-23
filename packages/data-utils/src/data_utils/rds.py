import os
from contextlib import contextmanager

import psycopg2
import structlog
from omegaconf import DictConfig

logger = structlog.get_logger()


def get_db_config_from_env() -> DictConfig:
    """Creates a database configuration from standard PostgreSQL environment variables.

    Reads: PGHOST, PGPORT (default 5432), PGUSER, PGPASSWORD, PGDATABASE.
    """
    return DictConfig(
        {
            "host": os.getenv("PGHOST"),
            "port": int(os.getenv("PGPORT", 5432)),
            "user": os.getenv("PGUSER"),
            "password": os.getenv("PGPASSWORD"),
            "dbname": os.getenv("PGDATABASE"),
        }
    )


@contextmanager
def db_connection(db_config: DictConfig | dict | None = None, raise_on_error: bool = False):
    """Context manager for PostgreSQL connections.

    Args:
        db_config: Database config with keys host, port, user, password, dbname.
            If None, reads from environment variables via get_db_config_from_env().
        raise_on_error: If True, raises on missing config or connection failure.
            If False, yields None and logs the error.

    Yields:
        psycopg2 connection, or None if connection could not be established.

    Raises:
        ValueError: If config is incomplete and raise_on_error is True.
        psycopg2.OperationalError: If connection fails and raise_on_error is True.
    """
    if db_config is None:
        db_config = get_db_config_from_env()

    required_keys = ["host", "user", "password", "dbname"]
    if not all(db_config.get(key) for key in required_keys):
        logger.error("Database configuration is incomplete. Please set PGHOST, PGUSER, PGPASSWORD, PGDATABASE.")
        if raise_on_error:
            raise ValueError("Database configuration is incomplete. Please set PGHOST, PGUSER, PGPASSWORD, PGDATABASE.")
        yield None
        return

    conn = None
    try:
        # Convert DictConfig to dict and filter out None values for psycopg2.connect compatibility.
        if isinstance(db_config, DictConfig):
            config_dict = {str(k): v for k, v in dict(db_config).items() if v is not None}
        else:
            config_dict = db_config
        conn = psycopg2.connect(**config_dict)
        yield conn
    except psycopg2.OperationalError as e:
        if raise_on_error:
            raise
        logger.error("Could not connect to PostgreSQL database.", error=str(e))
        yield None
    finally:
        if conn:
            conn.close()
