from unittest.mock import MagicMock, patch

import pytest
from omegaconf import OmegaConf
from psycopg2 import OperationalError

from data_utils.rds import db_connection, get_db_config_from_env


@pytest.fixture
def mock_db_config():
    """Pytest fixture for a mocked database configuration."""
    return OmegaConf.create(
        {
            "host": "mock_host",
            "port": 5432,
            "user": "mock_user",
            "password": "mock_password",
            "dbname": "mock_dbname",
        }
    )


@patch("data_utils.rds.psycopg2.connect")
def test_db_connection_success(mock_connect, mock_db_config):
    """Test successful database connection using the context manager."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    with db_connection(mock_db_config) as conn:
        assert conn == mock_conn
        mock_connect.assert_called_once_with(**mock_db_config)

    mock_conn.close.assert_called_once()


@patch("data_utils.rds.psycopg2.connect")
def test_db_connection_failure(mock_connect, mock_db_config):
    """Test database connection failure using the context manager."""
    mock_connect.side_effect = OperationalError("Mock connection error")
    with db_connection(mock_db_config) as conn:
        assert conn is None


def test_db_connection_incomplete_config():
    """Test that connection returns None with incomplete config."""
    incomplete_config = OmegaConf.create({"host": "mock_host"})
    with db_connection(incomplete_config) as conn:
        assert conn is None


@patch.dict(
    "os.environ",
    {
        "PGHOST": "env_host",
        "PGPORT": "5433",
        "PGUSER": "env_user",
        "PGPASSWORD": "env_password",
        "PGDATABASE": "env_db",
    },
)
def test_get_db_config_from_env():
    """Test reading database configuration from environment variables."""
    config = get_db_config_from_env()
    assert config.host == "env_host"
    assert config.port == 5433
    assert config.user == "env_user"
    assert config.password == "env_password"
    assert config.dbname == "env_db"


@patch("data_utils.rds.psycopg2.connect")
@patch("data_utils.rds.get_db_config_from_env")
def test_db_connection_uses_env_config(mock_get_config, mock_connect, mock_db_config):
    """Test that db_connection uses env config when none is provided."""
    mock_get_config.return_value = mock_db_config
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    with db_connection() as conn:
        assert conn is not None
        mock_get_config.assert_called_once()
        mock_connect.assert_called_once_with(**mock_db_config)

    mock_conn.close.assert_called_once()
