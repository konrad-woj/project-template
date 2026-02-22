from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from omegaconf import OmegaConf

from data_utils.ocr.ocr_fetcher import S3OcrFetcher


@pytest.fixture
def mock_db_config():
    """Database configuration for testing."""
    return OmegaConf.create(
        {
            "host": "test-host",
            "port": 5432,
            "user": "test-user",
            "password": "test-password",
            "dbname": "test-db",
        }
    )


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for testing."""
    return MagicMock()


@pytest.fixture
def s3_fetcher(mock_db_config, mock_s3_client):
    """S3OcrFetcher instance with mocked dependencies."""
    with patch("data_utils.ocr.ocr_fetcher.S3Client", return_value=mock_s3_client):
        fetcher = S3OcrFetcher(db_config=mock_db_config, ocr_s3_bucket="test-bucket")
        fetcher.s3_client = mock_s3_client
        return fetcher


class TestS3OcrFetcher:
    """Test suite for S3OcrFetcher class."""

    def test_init_with_custom_s3_client(self, mock_db_config, mock_s3_client):
        """Test initialization with provided S3 client."""
        fetcher = S3OcrFetcher(db_config=mock_db_config, s3_client=mock_s3_client, ocr_s3_bucket="custom-bucket")

        assert fetcher.s3_client == mock_s3_client
        assert fetcher.ocr_s3_bucket == "custom-bucket"

    @patch("data_utils.ocr.ocr_fetcher.S3Client")
    def test_init_without_s3_client(self, mock_s3_client_class, mock_db_config):
        """Test initialization without S3 client creates new instance."""
        fetcher = S3OcrFetcher(db_config=mock_db_config)

        mock_s3_client_class.assert_called_once()
        assert fetcher.s3_client is not None

    @pytest.mark.parametrize(
        "engine,expected_index",
        [
            ("RapidOcr", 0),
            ("Textract", 1),
            ("TextractOld", 2),
        ],
    )
    @patch("data_utils.ocr.ocr_fetcher.db_connection")
    def test_get_ocr_path_candidates_specific_engine(self, mock_db_conn, engine, expected_index, s3_fetcher):
        """Test fetching OCR path for specific engines."""

        mock_paths = ("rapid/path.json", "textract/path.json", "old/path.json")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = mock_paths
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_conn

        result = s3_fetcher.get_ocr_path_candidates_from_db("test.pdf", 1, engine)

        assert result == mock_paths[expected_index]

    @patch("data_utils.ocr.ocr_fetcher.db_connection")
    def test_get_ocr_path_candidates_all_engines(self, mock_db_conn, s3_fetcher):
        """Test fetching OCR paths for all engines."""

        mock_paths = ("rapid/path.json", "textract/path.json", "old/path.json")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = mock_paths
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_conn

        result = s3_fetcher.get_ocr_path_candidates_from_db("test.pdf", 1, "Any")

        assert result == mock_paths

    @patch("data_utils.ocr.ocr_fetcher.db_connection")
    def test_get_ocr_path_candidates_no_connection(self, mock_db_conn, s3_fetcher):
        """Test handling of missing database connection."""

        mock_db_conn.return_value.__enter__.return_value = None

        result = s3_fetcher.get_ocr_path_candidates_from_db("test.pdf", 1)

        assert result is None

    @patch("data_utils.ocr.ocr_fetcher.db_connection")
    def test_get_ocr_path_candidates_no_results(self, mock_db_conn, s3_fetcher):
        """Test handling when no database results found."""

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db_conn.return_value.__enter__.return_value = mock_conn

        result = s3_fetcher.get_ocr_path_candidates_from_db("missing.pdf", 1)

        assert result is None

    @patch("data_utils.ocr.ocr_fetcher.db_connection")
    def test_get_ocr_path_candidates_database_error(self, mock_db_conn, s3_fetcher):
        """Test handling of database errors."""

        mock_db_conn.side_effect = Exception("Database connection failed")

        result = s3_fetcher.get_ocr_path_candidates_from_db("test.pdf", 1)

        assert result is None

    def test_get_original_s3_path_success(self, s3_fetcher):
        """Test successful retrieval of original S3 path."""

        s3_fetcher.s3_client.s3_client.list_objects_v2.return_value = {
            "Contents": [{"Key": "source_paths_info/hash123/info.json"}]
        }
        s3_fetcher.s3_client.get_object.return_value = '{"original_path": "/docs/test.pdf"}'

        result = s3_fetcher.get_original_s3_path_from_hash("test-bucket", "hash123")

        assert result == "/docs/test.pdf"

    def test_get_original_s3_path_no_files(self, s3_fetcher):
        """Test handling when no source info files found."""

        s3_fetcher.s3_client.s3_client.list_objects_v2.return_value = {"Contents": []}

        result = s3_fetcher.get_original_s3_path_from_hash("test-bucket", "hash123")

        assert result is None

    def test_get_original_s3_path_no_json_files(self, s3_fetcher):
        """Test handling when no JSON files found in source info."""

        s3_fetcher.s3_client.s3_client.list_objects_v2.return_value = {
            "Contents": [{"Key": "source_paths_info/hash123/info.txt"}]
        }

        result = s3_fetcher.get_original_s3_path_from_hash("test-bucket", "hash123")

        assert result is None

    def test_get_original_s3_path_missing_original_path(self, s3_fetcher):
        """Test handling when original_path is missing from JSON."""

        s3_fetcher.s3_client.s3_client.list_objects_v2.return_value = {
            "Contents": [{"Key": "source_paths_info/hash123/info.json"}]
        }
        s3_fetcher.s3_client.get_object.return_value = '{"other_field": "value"}'

        result = s3_fetcher.get_original_s3_path_from_hash("test-bucket", "hash123")

        assert result is None

    def test_get_original_s3_path_client_error(self, s3_fetcher):
        """Test handling of S3 client errors."""

        s3_fetcher.s3_client.s3_client.list_objects_v2.side_effect = ClientError({}, "ListObjects")

        result = s3_fetcher.get_original_s3_path_from_hash("test-bucket", "hash123")

        assert result is None

    def test_fetch_ocr_results_success(self, s3_fetcher):
        """Test successful OCR results fetching."""

        s3_fetcher.get_original_s3_path_from_hash = MagicMock(return_value="/docs/test.pdf")
        s3_fetcher.get_ocr_path_candidates_from_db = MagicMock(
            return_value=("bucket/rapid.json", "bucket/textract.json", "bucket/old.json")
        )
        s3_fetcher.s3_client.get_object.return_value = (
            '{"Blocks": [{"text": "test", "Geometry": {"Polygon": [{"X": 0, "Y": 0}, {"X": 1, "Y": 0}]}}]}'
        )

        result = s3_fetcher.fetch_ocr_results_by_hash("hash123")

        assert result == [{"text": "test", "Geometry": {"Polygon": [{"X": 0, "Y": 0}, {"X": 1, "Y": 0}]}}]
        s3_fetcher.s3_client.get_object.assert_called_once_with(
            bucket="bucket", key_name="rapid.json", content_only=True, decode_content=True
        )

    def test_fetch_ocr_results_engine_fallback(self, s3_fetcher):
        """Test fallback to next engine when first fails."""

        s3_fetcher.get_original_s3_path_from_hash = MagicMock(return_value="/docs/test.pdf")
        s3_fetcher.get_ocr_path_candidates_from_db = MagicMock(
            return_value=("bucket/rapid.json", "bucket/textract.json", "bucket/old.json")
        )
        s3_fetcher.s3_client.get_object.side_effect = [
            Exception("First engine failed"),
            '{"Blocks": [{"text": "fallback", "Geometry": {"Polygon": [{"X": 0, "Y": 0}, {"X": 1, "Y": 0}]}}]}',
        ]

        result = s3_fetcher.fetch_ocr_results_by_hash("hash123")

        assert result == [{"text": "fallback", "Geometry": {"Polygon": [{"X": 0, "Y": 0}, {"X": 1, "Y": 0}]}}]
        assert s3_fetcher.s3_client.get_object.call_count == 2

    def test_fetch_ocr_results_no_original_path(self, s3_fetcher):
        """Test handling when original path not found."""

        s3_fetcher.get_original_s3_path_from_hash = MagicMock(return_value=None)

        result = s3_fetcher.fetch_ocr_results_by_hash("hash123")

        assert result is None

    def test_fetch_ocr_results_no_candidates(self, s3_fetcher):
        """Test handling when no OCR candidates found."""

        s3_fetcher.get_original_s3_path_from_hash = MagicMock(return_value="/docs/test.pdf")
        s3_fetcher.get_ocr_path_candidates_from_db = MagicMock(return_value=None)

        result = s3_fetcher.fetch_ocr_results_by_hash("hash123")

        assert result is None

    def test_fetch_ocr_results_all_engines_fail(self, s3_fetcher):
        """Test handling when all OCR engines fail."""

        s3_fetcher.get_original_s3_path_from_hash = MagicMock(return_value="/docs/test.pdf")
        s3_fetcher.get_ocr_path_candidates_from_db = MagicMock(
            return_value=("bucket/rapid.json", "bucket/textract.json", "bucket/old.json")
        )
        s3_fetcher.s3_client.get_object.side_effect = Exception("All engines failed")

        result = s3_fetcher.fetch_ocr_results_by_hash("hash123")

        assert result is None
        assert s3_fetcher.s3_client.get_object.call_count == 3
