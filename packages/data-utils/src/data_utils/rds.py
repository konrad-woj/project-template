import os
from contextlib import contextmanager

import psycopg2
import structlog
from omegaconf import DictConfig

logger = structlog.get_logger()


def get_db_config_from_env():
    """Creates a database configuration from standard PostgreSQL environment variables."""
    return DictConfig(
        {
            # TODO: Update after moving to production.
            "host": os.getenv("PGHOST", "hermes-dev-hermesmain-postgres.coaneyfgilms.eu-central-1.rds.amazonaws.com"),
            "port": int(os.getenv("PGPORT", 5432)),
            "user": os.getenv("PGUSER", "postgres"),
            "password": os.getenv("PGPASSWORD"),  # TODO: Update to read workflow variable.
            "dbname": os.getenv("PGDATABASE", "hermes-ops-dev-demo2"),
        }
    )


@contextmanager
def db_connection(db_config: DictConfig | dict | None = None, raise_on_error: bool = False):
    """
    A context manager for database connections.

    It ensures that the connection is properly closed.
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
