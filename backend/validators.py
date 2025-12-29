from fastapi import HTTPException
from typing import List

# Allowed video file extensions
ALLOWED_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']

# Allowed MIME types
ALLOWED_MIME_TYPES = [
    'video/mp4',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-matroska',
    'video/webm'
]

MAX_TITLE_LENGTH = 255
MIN_TITLE_LENGTH = 3


def validate_file_extension(filename: str) -> bool:
    """Check if file has allowed extension"""
    import os
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def validate_title(title: str) -> tuple[bool, str]:
    """Validate video title"""
    if not title or len(title.strip()) == 0:
        return False, "Title cannot be empty"
    
    if len(title) < MIN_TITLE_LENGTH:
        return False, f"Title must be at least {MIN_TITLE_LENGTH} characters"
    
    if len(title) > MAX_TITLE_LENGTH:
        return False, f"Title must be at most {MAX_TITLE_LENGTH} characters"
    
    # Check for invalid characters
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        if char in title:
            return False, f"Title contains invalid character: {char}"
    
    return True, ""


def validate_upload_request(filename: str, title: str, file_size: int) -> None:
    """
    Validate entire upload request
    Raises HTTPException if invalid
    """
    # Check extension
    if not validate_file_extension(filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate title
    is_valid, error = validate_title(title)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Size already validated in file_utils, but double-check
    from file_utils import MAX_FILE_SIZE_BYTES
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum: {MAX_FILE_SIZE_BYTES / (1024*1024)}MB"
        )