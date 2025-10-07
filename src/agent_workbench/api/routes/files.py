"""File upload/download endpoints for persistent file storage."""

import logging
import os
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


class FileMetadata(BaseModel):
    """File metadata response."""

    file_id: str
    filename: str
    size: int
    content_type: str
    uploaded_at: datetime
    url: str


class FileListResponse(BaseModel):
    """List of uploaded files."""

    files: List[FileMetadata]
    total: int


# File storage configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/agent_workbench_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_file_path(file_id: str) -> str:
    """Get absolute file path from file ID."""
    return os.path.join(UPLOAD_DIR, file_id)


def _save_file_metadata(file_id: str, filename: str, size: int, content_type: str):
    """Save file metadata to Hub DB."""
    from ..hub_database import create_hub_database

    hub_db = create_hub_database()
    hub_db.set_value(
        key=file_id,
        value={
            "filename": filename,
            "size": size,
            "content_type": content_type,
            "uploaded_at": datetime.utcnow().isoformat(),
        },
        table="file_metadata",
    )


def _get_file_metadata(file_id: str) -> Optional[dict]:
    """Get file metadata from Hub DB."""
    from ..hub_database import create_hub_database

    hub_db = create_hub_database()
    return hub_db.get_value(key=file_id, table="file_metadata")


@router.post("/upload", response_model=FileMetadata)
async def upload_file(file: UploadFile = File(...)) -> FileMetadata:
    """
    Upload a file to persistent storage.

    Supports:
    - Documents (PDF, TXT, DOCX)
    - Images (PNG, JPG, GIF)
    - Data files (CSV, JSON, XLSX)
    - Any other file type

    Files are stored both locally and metadata in Hub DB for persistence.
    """
    logger.info("=" * 80)
    logger.info("📤 FILE UPLOAD REQUEST")
    logger.info(f"📄 Filename: {file.filename}")
    logger.info(f"📊 Content-Type: {file.content_type}")
    logger.info("=" * 80)

    try:
        # Generate unique file ID
        file_id = f"{uuid4()}_{file.filename}"
        file_path = _get_file_path(file_id)

        # Save file to disk
        logger.info(f"💾 Saving to {file_path}")
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        file_size = len(content)
        logger.info(f"✅ Saved {file_size} bytes")

        # Save metadata to Hub DB
        _save_file_metadata(
            file_id=file_id,
            filename=file.filename,
            size=file_size,
            content_type=file.content_type or "application/octet-stream",
        )

        logger.info(f"✅ File uploaded successfully: {file_id}")
        logger.info("=" * 80)

        return FileMetadata(
            file_id=file_id,
            filename=file.filename,
            size=file_size,
            content_type=file.content_type or "application/octet-stream",
            uploaded_at=datetime.utcnow(),
            url=f"/api/v1/files/download/{file_id}",
        )

    except Exception as e:
        logger.error(f"❌ File upload failed: {str(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    Download a previously uploaded file.

    Returns the file with appropriate Content-Type and Content-Disposition headers.
    """
    logger.info(f"📥 File download request: {file_id}")

    try:
        # Get file metadata
        metadata = _get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")

        # Check if file exists on disk
        file_path = _get_file_path(file_id)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        logger.info(f"✅ Serving file: {metadata['filename']}")

        # Return file with original filename
        return FileResponse(
            path=file_path,
            media_type=metadata["content_type"],
            filename=metadata["filename"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ File download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")


@router.get("/list", response_model=FileListResponse)
async def list_files() -> FileListResponse:
    """
    List all uploaded files with metadata.

    Returns metadata for all files stored in Hub DB.
    """
    logger.info("📋 Listing all uploaded files")

    try:
        from ..hub_database import create_hub_database

        hub_db = create_hub_database()
        df = hub_db._get_table("file_metadata")

        files = []
        for _, row in df.iterrows():
            file_id = row["id"]
            import json

            metadata = json.loads(row["value"])

            files.append(
                FileMetadata(
                    file_id=file_id,
                    filename=metadata["filename"],
                    size=metadata["size"],
                    content_type=metadata["content_type"],
                    uploaded_at=metadata["uploaded_at"],
                    url=f"/api/v1/files/download/{file_id}",
                )
            )

        logger.info(f"✅ Found {len(files)} files")
        return FileListResponse(files=files, total=len(files))

    except Exception as e:
        logger.error(f"❌ File listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File listing failed: {str(e)}")


@router.delete("/delete/{file_id}")
async def delete_file(file_id: str):
    """
    Delete a file from storage.

    Removes both the file from disk and its metadata from Hub DB.
    """
    logger.info(f"🗑️ File deletion request: {file_id}")

    try:
        # Check if file exists
        metadata = _get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")

        # Delete from disk
        file_path = _get_file_path(file_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"✅ Deleted file from disk: {file_path}")

        # Delete metadata from Hub DB
        from ..hub_database import create_hub_database

        hub_db = create_hub_database()
        df = hub_db._get_table("file_metadata")
        df = df[df["id"] != file_id]
        hub_db._save_table("file_metadata", df)

        logger.info(f"✅ File deleted successfully: {file_id}")
        return {"status": "success", "message": f"File {file_id} deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ File deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")


@router.get("/health")
async def files_health():
    """Health check for file management service."""
    return {
        "status": "healthy",
        "service": "file_management",
        "upload_dir": UPLOAD_DIR,
        "upload_dir_exists": os.path.exists(UPLOAD_DIR),
        "endpoints": ["/upload", "/download/{file_id}", "/list", "/delete/{file_id}"],
    }
