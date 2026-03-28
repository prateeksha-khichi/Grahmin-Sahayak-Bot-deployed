"""
File utilities - Handle file operations (uploads + temp cleanup + project dirs)
"""

import os
import shutil
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from loguru import logger
from config import get_settings

settings = get_settings()


# ===============================
# Directory Utilities
# ===============================

def ensure_directory(path: str):
    """Create directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)
    logger.debug(f"📁 Directory ensured: {path}")


def init_project_directories():
    """Create all required project directories"""

    directories = [
        settings.upload_dir,
        'data/pdfs',
        'data/processed',
        'data/processed/faiss_index',
        'models/loan_eligibility',
        'models/fraud_detection',
        'models/embeddings',
        'logs',
        'temp_audio'
    ]

    for directory in directories:
        ensure_directory(directory)

    logger.info("✅ All project directories initialized")


# ===============================
# Upload + File Handling
# ===============================

async def save_uploaded_file(file: UploadFile) -> str:
    """
    Save uploaded file and return path
    """

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    max_size = settings.max_file_size_mb * 1024 * 1024

    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.max_file_size_mb}MB"
        )

    ext = Path(file.filename).suffix.lower()
    filename = f"{uuid.uuid4()}{ext}"
    file_path = upload_dir / filename

    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    logger.info(f"📄 Uploaded file saved: {file_path}")

    return str(file_path)


def validate_file_type(filename: str, allowed_types: list) -> bool:
    """Check if file extension is allowed"""
    ext = Path(filename).suffix.lower()
    return ext in allowed_types


def get_file_size_mb(filepath: str) -> float:
    """Get file size in MB"""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0.0


def safe_file_delete(filepath: str):
    """Safely delete a file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"🗑️ Deleted: {filepath}")
    except Exception as e:
        logger.warning(f"⚠️ Could not delete {filepath}: {e}")


# ===============================
# Temp Cleanup
# ===============================

def cleanup_temp_files(directory: str = "temp_audio", max_age_hours: int = 24):
    """
    Delete old temporary files
    """

    import time

    if not os.path.exists(directory):
        return

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    deleted_count = 0

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        if os.path.isfile(filepath):
            file_age = current_time - os.path.getmtime(filepath)

            if file_age > max_age_seconds:
                os.remove(filepath)
                deleted_count += 1

    if deleted_count > 0:
        logger.info(f"🧹 Cleaned {deleted_count} temp files from {directory}")


# ===============================
# Backup Copy Utility
# ===============================

def copy_with_backup(source: str, destination: str):
    """Copy file with backup of existing destination"""

    if os.path.exists(destination):
        backup = f"{destination}.backup"
        shutil.copy2(destination, backup)
        logger.info(f"💾 Backup created: {backup}")

    shutil.copy2(source, destination)
    logger.info(f"📋 Copied: {source} -> {destination}")


# ===============================
# Manual Init
# ===============================

if __name__ == "__main__":
    init_project_directories()

class FileUtils:
    @staticmethod
    def read_text(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def exists(path: str) -> bool:
        return os.path.exists(path)
