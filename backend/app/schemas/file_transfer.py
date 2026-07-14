"""
Mission Control File Transfer API Schemas

Sprint 2.1.8 - Remote Operations Finalization.
"""

from pydantic import BaseModel
from pydantic import Field


class FileUploadRequest(BaseModel):
    """Payload for uploading a file to a remote host."""

    host_id: int
    remote_path: str = Field(..., min_length=1, description="Destination path on remote host.")
    content_base64: str = Field(..., min_length=1, description="File content encoded as base64.")


class FileDownloadRequest(BaseModel):
    """Payload for downloading a file from a remote host."""

    host_id: int
    remote_path: str = Field(..., min_length=1)


class FileTransferResponse(BaseModel):
    """Result of a file transfer operation."""

    success: bool
    message: str
    remote_path: str
    size_bytes: int | None = None


class FileDownloadResponse(BaseModel):
    """Result of a file download."""

    success: bool
    message: str
    remote_path: str
    content_base64: str | None = None
    size_bytes: int | None = None


class FileListItem(BaseModel):
    """A single file or directory entry."""

    name: str
    path: str
    is_directory: bool
    size_bytes: int | None = None
    modified_at: str | None = None
    permissions: str | None = None


class FileListResponse(BaseModel):
    """Response for listing remote directory contents."""

    path: str
    items: list[FileListItem]


class FileDeleteRequest(BaseModel):
    """Payload for deleting a file on a remote host."""

    host_id: int
    remote_path: str = Field(..., min_length=1)


class FileMkdirRequest(BaseModel):
    """Payload for creating a directory on a remote host."""

    host_id: int
    remote_path: str = Field(..., min_length=1)
