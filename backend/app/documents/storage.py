import contextlib
import os
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles

from app.config import settings


class StorageProvider(ABC):
    """Abstract storage service for document files."""

    @abstractmethod
    async def save_file(self, tenant_id: int, document_id: int, file_data: bytes, filename: str) -> str:
        """Save file data and return the storage path. filename sets the extension."""

    @abstractmethod
    def get_file_url(self, tenant_id: int, document_id: int, filename: str) -> str:
        """Return the filesystem path / URL to retrieve the file."""

    @abstractmethod
    async def read_file(self, tenant_id: int, document_id: int, filename: str) -> bytes:
        """Return the raw bytes of a stored file. Raises FileNotFoundError if absent."""

    @abstractmethod
    async def delete_file(self, tenant_id: int, document_id: int, filename: str) -> None:
        """Delete a stored file. No error if it does not exist."""


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage with per-workspace isolation."""

    def __init__(self, base_path: str = "./uploads"):
        self.base_path = Path(base_path).resolve()

    def _path(self, tenant_id: int, document_id: int, filename: str) -> Path:
        # Confined to base_path/tenant_{id}/; document_id is an int and only the
        # filename suffix is used, so there is no path-traversal risk.
        ext = Path(filename).suffix
        return self.base_path / f"tenant_{tenant_id}" / f"{document_id}{ext}"

    async def save_file(self, tenant_id: int, document_id: int, file_data: bytes, filename: str) -> str:
        tenant_dir = self.base_path / f"tenant_{tenant_id}"
        tenant_dir.mkdir(parents=True, exist_ok=True)
        file_path = self._path(tenant_id, document_id, filename)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_data)
        return str(file_path)

    def get_file_url(self, tenant_id: int, document_id: int, filename: str) -> str:
        return str(self._path(tenant_id, document_id, filename))

    async def read_file(self, tenant_id: int, document_id: int, filename: str) -> bytes:
        async with aiofiles.open(self._path(tenant_id, document_id, filename), "rb") as f:
            return await f.read()

    async def delete_file(self, tenant_id: int, document_id: int, filename: str) -> None:
        with contextlib.suppress(FileNotFoundError):
            os.remove(self._path(tenant_id, document_id, filename))


def get_storage_provider() -> StorageProvider:
    """Return the configured storage provider."""
    if settings.STORAGE_PROVIDER == "local":
        return LocalStorageProvider(settings.STORAGE_LOCAL_PATH)
    raise ValueError(f"Unknown storage provider: {settings.STORAGE_PROVIDER}")
