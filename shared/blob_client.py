import io
import logging
import os
from typing import Optional

from azure.storage.blob import BlobServiceClient, ContainerClient

logger = logging.getLogger(__name__)


class BlobClient:
    """Azure Blob Storage client for the paper-analyzer pipeline."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        container_name: Optional[str] = None,
    ):
        self._connection_string = connection_string or os.getenv("AZURE_CONNECTION_STRING", "")
        self._container_name = container_name or os.getenv("AZURE_CONTAINER_NAME", "papers")

        if not self._connection_string:
            raise ValueError("AZURE_CONNECTION_STRING is required")

        self._service_client = BlobServiceClient.from_connection_string(self._connection_string)
        self._container_client = self._service_client.get_container_client(self._container_name)
        self._ensure_container()

    def _ensure_container(self) -> None:
        try:
            self._container_client.get_container_properties()
        except Exception:
            self._container_client.create_container()
            logger.info(f"Created container: {self._container_name}")

    def upload_file(self, local_path: str, blob_name: str, overwrite: bool = True) -> str:
        """Upload a local file to blob storage. Returns the blob URL."""
        blob_client = self._container_client.get_blob_client(blob_name)
        with open(local_path, "rb") as f:
            blob_client.upload_blob(f, overwrite=overwrite)
        logger.info(f"Uploaded {local_path} -> {blob_name}")
        return blob_client.url

    def upload_bytes(self, data: bytes, blob_name: str, overwrite: bool = True) -> str:
        """Upload raw bytes to blob storage. Returns the blob URL."""
        blob_client = self._container_client.get_blob_client(blob_name)
        blob_client.upload_blob(data, overwrite=overwrite)
        logger.info(f"Uploaded {len(data)} bytes -> {blob_name}")
        return blob_client.url

    def upload_json(self, obj: dict, blob_name: str, overwrite: bool = True) -> str:
        """Serialize a dict to JSON and upload it. Returns the blob URL."""
        import json
        data = json.dumps(obj, indent=2, default=str).encode("utf-8")
        return self.upload_bytes(data, blob_name, overwrite=overwrite)

    def download_bytes(self, blob_name: str) -> bytes:
        """Download a blob as raw bytes."""
        blob_client = self._container_client.get_blob_client(blob_name)
        return blob_client.download_blob().readall()

    def download_json(self, blob_name: str) -> dict:
        """Download a blob and parse it as JSON."""
        import json
        return json.loads(self.download_bytes(blob_name))

    def download_to_file(self, blob_name: str, local_path: str) -> None:
        """Download a blob to a local file."""
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        blob_client = self._container_client.get_blob_client(blob_name)
        with open(local_path, "wb") as f:
            f.write(blob_client.download_blob().readall())
        logger.info(f"Downloaded {blob_name} -> {local_path}")

    def list_blobs(self, prefix: Optional[str] = None) -> list[str]:
        """List blob names, optionally filtered by prefix."""
        return [b.name for b in self._container_client.list_blobs(name_starts_with=prefix)]

    def exists(self, blob_name: str) -> bool:
        """Check if a blob exists."""
        blob_client = self._container_client.get_blob_client(blob_name)
        return blob_client.exists()

    def delete(self, blob_name: str) -> None:
        """Delete a blob."""
        blob_client = self._container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
        logger.info(f"Deleted blob: {blob_name}")
