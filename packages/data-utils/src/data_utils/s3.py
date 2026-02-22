import asyncio
from fnmatch import fnmatch
from pathlib import Path

import aiofiles
import boto3
import structlog
from botocore.exceptions import ClientError

logger = structlog.get_logger()


def is_s3_path(path: Path | str) -> bool:
    return str(path).startswith("s3://")


class S3Client:
    """S3 client for uploading and downloading files."""

    def __init__(self, *args, **kwargs):
        self.s3_client = boto3.client("s3", *args, **kwargs)

    @staticmethod
    def parse_s3_path(s3_path: Path | str) -> tuple[str, str]:
        """Returns bucket and key from full S3 path.

        Args:
            s3_path: Path formatted like s3://bucket_name/folder1/folder2/file1.json

        Returns:
            Tuple of bucket name and key (path).
        """
        s3_path = str(s3_path)
        s3_path = s3_path.replace("s3://", "")
        bucket, key = s3_path.split("/", 1)
        return bucket, key

    def check_bucket_connection(self, bucket_name: str) -> bool:
        """Check if a connection to the specified S3 bucket can be established.
        Tries to access the S3 bucket using a lightweight operation to verify that the client
        has the necessary permissions and the bucket exists. Returns True if the connection
        is successful, otherwise returns False.

        Args:
            bucket_name (str): The name of the S3 bucket to check.

        Returns:
            bool: True if the connection to the S3 bucket is successful, False otherwise.
        """

        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    def file_exists(self, s3_path: str) -> bool:
        """Returns True if the file exists in S3.

        Args:
            s3_path: Path formatted like s3://bucket_name/folder1/folder2/file1.json

        Returns:
            True if the file exists, False otherwise.
        """
        bucket, key = self.parse_s3_path(s3_path)
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    def dir_exists(self, s3_path: str) -> bool:
        """Checks if a directory exists in S3.

        Args:
            s3_path: Path formatted like s3://bucket_name/folder1/folder2/

        Returns:
            True if the directory exists, False otherwise.
        """
        bucket, key = self.parse_s3_path(s3_path)
        # Strips off the last / from path. This prefix will check just that folder and doesn't check within that folder.
        key = key.rstrip("/")
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=key, Delimiter="/")
            return "CommonPrefixes" in response and len(response["CommonPrefixes"]) > 0
        except ClientError:
            return False

    def list_matching_files(self, bucket: str, path: str, pattern: str = "*") -> list[str]:
        """Lists all S3 file paths in a bucket that match a pattern.

        Args:
            bucket: S3 bucket name.
            path: S3 path prefix to filter objects.
            pattern: File pattern to match, e.g. "*", "*.pdf", "hermes*".

        Returns:
            List of S3 keys (paths) that match the pattern.
        """
        matching_files = []

        # List objects in the bucket with the specified prefix
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix=path)

        for page in pages:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                key = obj["Key"]
                filename = Path(key).name

                if fnmatch(filename, pattern):
                    matching_files.append(key)

        if not matching_files:
            logger.info(f"No files matching '{pattern}' found.", bucket=bucket, path=path)

        return matching_files

    def get_last_modify(self, bucket: str, key: str) -> str:
        """
        Retrieves the LastModified timestamp of an object in S3.

        Args:
            bucket (str): The name of the S3 bucket.
            key (str): The key (path) of the object in the S3 bucket.

        Returns:
            str: The ISO 8601 formatted LastModified timestamp of the object.

        Raises:
            botocore.exceptions.ClientError: If the object does not exist or access is denied.

        Example:
            s3_client = S3Client(...)
            last_modified = s3_client.get_last_modify('my-bucket', 'folder/my-object.txt')
        """
        head = self.s3_client.head_object(Bucket=bucket, Key=key)
        return head["LastModified"].isoformat()

    def get_object(
        self, bucket: str, key_name: str, content_only: bool = True, decode_content: bool = False
    ) -> bytes | str:
        """Gets an object from S3.

        Args:
            bucket: S3 bucket name.
            key_name: S3 object key (path).
            content_only: If True, return only the content of the object.
            decode_content: If True, decode the content to UTF-8.

        Returns:
            The S3 object or its content.
        """
        logger.info("Getting object from S3...", bucket=bucket, key=key_name)
        obj = self.s3_client.get_object(Bucket=bucket, Key=key_name)

        if content_only:
            return obj["Body"].read().decode("utf-8") if decode_content else obj["Body"].read()

        return obj

    async def get_object_async(
        self, bucket: str, key_name: str, content_only: bool = True, decode_content: bool = False
    ) -> bytes | str:
        """Gets an object from S3 asynchronously.

        Args:
            bucket: S3 bucket name.
            key_name: S3 object key (path).
            content_only: If True, return only the content of the object.
            decode_content: If True, decode the content to UTF-8.

        Returns:
            The S3 object or its content.
        """
        logger.info("Getting object from S3...", bucket=bucket, key=key_name)
        obj = await asyncio.to_thread(self.s3_client.get_object, Bucket=bucket, Key=key_name)

        if content_only:
            return obj["Body"].read().decode("utf-8") if decode_content else obj["Body"].read()

        return obj

    def download_file(self, bucket: str, key_name: str, dest_dir: str | Path) -> None:
        """Downloads a file from S3 to a local directory.

        Args:
            bucket: S3 bucket name.
            key_name: S3 object key (path).
            dest_dir: Destination directory.
        """
        logger.info("Downloading file from S3...", bucket=bucket, key=key_name, dest_dir=dest_dir)
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / Path(key_name).name
        self.s3_client.download_file(bucket, key_name, str(dest_file))

    async def download_file_async(self, bucket: str, key: str, dest_dir: str | Path) -> str | None:
        """Downloads a file from S3 to a local directory asynchronously.

        Args:
            bucket: S3 bucket name.
            key: S3 object key (path).
            dest_dir: Destination directory.

        Returns:
            The path of the downloaded file or None if download failed.
        """
        logger.info("Downloading file from S3...", bucket=bucket, key=key, dest_dir=dest_dir)
        dest_file = Path(dest_dir) / Path(key).name
        try:
            await asyncio.to_thread(self.s3_client.download_file, bucket, key, str(dest_file))
            return str(dest_file)
        except Exception as e:
            logger.error("Failed to download file.", bucket=bucket, key=key, error=str(e))
            return None

    async def download_files(
        self, bucket: str, path: str, pattern: str = "*", dest_dir: str | Path | None = None
    ) -> list[str]:
        """Downloads all files from S3 to a local directory asynchronously.

        Args:
            bucket: S3 bucket name.
            path: S3 path prefix to filter objects.
            pattern: File pattern to match, e.g. "*", "*.pdf", "hermes*".
            dest_dir: Destination directory. If None, will use current working directory.

        Returns:
            List of downloaded file paths.
        """
        matching_paths = self.list_matching_files(bucket, path, pattern)

        if not matching_paths:
            logger.warning(f"No files matching '{pattern}'.", bucket=bucket, key=path)
            return []

        dest_dir = Path(dest_dir or Path.cwd() / f"{bucket}")
        dest_dir.mkdir(parents=True, exist_ok=True)

        tasks = [self.download_file_async(bucket, key, dest_dir) for key in matching_paths]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        downloaded_files = [f for f in results if f is not None]
        logger.info(
            f"Downloaded {len(downloaded_files)} of {len(matching_paths)} files.",
            bucket=bucket,
            key=path,
            dest_dir=dest_dir,
        )
        return downloaded_files

    def put_object(self, bucket: str, key_name: str, object_bytes: bytes, overwrite: bool = True) -> str | None:
        """Uploads bytes object to S3.

        Args:
            bucket: S3 bucket name.
            key_name: S3 object key (path).
            object_bytes: Bytes object to upload.
            overwrite: If False, skip uploading files that already exist in S3.

        Returns:
            S3 path where the object was uploaded.
        """
        if not overwrite and self.file_exists(f"s3://{bucket}/{key_name}"):
            logger.info("File already exists. Skipping upload.", bucket=bucket, key=key_name)
            return None

        try:
            logger.info("Uploading to file to S3...", bucket=bucket, key=key_name, overwrite=overwrite)
            self.s3_client.put_object(Bucket=bucket, Key=key_name, Body=object_bytes)
            return f"s3://{bucket}/{key_name}"
        except ClientError:
            logger.error("Failed to upload file to S3.", bucket=bucket, key=key_name)
            raise

    async def upload_files(
        self, src_dir: str | Path, bucket: str, path: str, pattern: str = "*", overwrite: bool = False
    ) -> list[str]:
        """Upload all files matching a given pattern from subdirs to S3.

        Args:
            src_dir: Source local directory, where files are located.
            bucket: Destination S3 bucket name.
            path: Destination S3 path, that comes after bucket name, e.g. "dir1/dir2". If src_dir has subdirs, they will
                be appended to this path and result in e.g., s3://bucket/dir1/dir2/src_subdir/file.pdf .
            pattern: File pattern to match, e.g. "*", "*.pdf", "hermes*".
            overwrite: If False, skip uploading files that already exist in S3.
        """
        src_dir_path = Path(src_dir)
        matching_paths = list(src_dir_path.rglob(pattern))
        tasks = []
        for src_file in matching_paths:
            if src_file.is_file():
                async with aiofiles.open(src_file, "rb") as f:
                    file_content = await f.read()
                    key = f"{path}/{src_file.relative_to(src_dir_path)}"
                    tasks.append(asyncio.to_thread(self.put_object, bucket, key, file_content, overwrite))
        results = await asyncio.gather(*tasks)
        uploaded_files = [f for f in results if f is not None]
        logger.info(
            f"Uploaded {len(uploaded_files)} of {len(matching_paths)} files.",
            bucket=bucket,
            key=path,
            src_dir=src_dir,
            overwrite=overwrite,
        )
        return uploaded_files
