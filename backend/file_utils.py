import os
import uuid
from datetime import datetime
from typing import Optional
import aiofiles

# File size limits
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate unique filename to avoid collisions
    
    Args:
        original_filename: User's original filename
        
    Returns:
        Unique filename with timestamp and UUID
    """
    # Get file extension
    _, ext = os.path.splitext(original_filename)
    
    # Generate unique name: timestamp_uuid.ext
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]  # First 8 chars of UUID
    
    return f"{timestamp}_{unique_id}{ext}"


def sanitize_filename(filename: str) -> str:
    """
    Remove potentially dangerous characters from filename
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators and dangerous characters
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    
    sanitized = filename
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    return sanitized


def format_file_size(size_bytes: int) -> str:
    """
    Format bytes into human-readable size
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "15.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


async def save_upload_file_tmp(upload_file) -> str:
    """
    Save uploaded file to temporary location
    
    Args:
        upload_file: FastAPI UploadFile object
        
    Returns:
        Path to temporary file
    """
    # Create temp directory if doesn't exist
    tmp_dir = "/tmp/streamscribe_uploads"
    os.makedirs(tmp_dir, exist_ok=True)
    
    # Generate temp filename
    tmp_filename = generate_unique_filename(upload_file.filename)
    tmp_path = os.path.join(tmp_dir, tmp_filename)
    
    # Write file in chunks (memory efficient)
    async with aiofiles.open(tmp_path, 'wb') as out_file:
        while content := await upload_file.read(1024 * 1024):  # Read 1MB at a time
            await out_file.write(content)
    
    return tmp_path


def validate_file_size(file_size: int) -> tuple[bool, Optional[str]]:
    """
    Validate file size is within limits
    
    Args:
        file_size: Size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, None

