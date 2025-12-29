from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional
try:
    import magic
except ImportError:
    magic = None

import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "videos")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_file_type(file_data: bytes) -> str:
    """
    Detect file type from binary data using magic numbers
    """
    try:
        if magic is None:
            logger.warning("python-magic not available, using default type")
            return "application/octet-stream"
        
        # Try the method that works on both Mac and Linux
        mime = magic.Magic(mime=True)
        return mime.from_buffer(file_data)
    except Exception as e:
        logger.error(f"Error detecting file type: {e}")
        return "application/octet-stream"


def is_video_file(mime_type: str) -> bool:
    """
    Check if MIME type is a video
    
    Args:
        mime_type: MIME type string
        
    Returns:
        True if video, False otherwise
    """
    allowed_types = [
        'video/mp4',
        'video/quicktime',  # .mov
        'video/x-msvideo',  # .avi
        'video/x-matroska', # .mkv
        'video/webm'
    ]
    return mime_type in allowed_types


async def upload_to_storage(
    file_data: bytes,
    filename: str,
    folder: str = "uploads"
) -> dict:
    try:
        storage_path = f"{folder}/{filename}"
        mime_type = get_file_type(file_data[:2048])
        
        # Upload to Supabase Storage
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file_data,
            file_options={
                "content-type": mime_type,
                "upsert": "true"  # ADD THIS - allows overwriting
            }
        )
        
        # Get public URL (works because bucket is public now)
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)
        
        logger.info(f"File uploaded successfully: {storage_path}")
        
        return {
            "success": True,
            "storage_path": storage_path,
            "file_url": public_url,  # Changed from constructed URL
            "mime_type": mime_type
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def delete_from_storage(storage_path: str) -> bool:
    """
    Delete file from Supabase Storage
    
    Args:
        storage_path: Path in storage bucket
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.storage.from_(SUPABASE_BUCKET).remove([storage_path])
        logger.info(f"File deleted: {storage_path}")
        return True
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return False


def get_signed_url(storage_path: str, expires_in: int = 3600) -> Optional[str]:
    """
    Generate signed URL for private file access
    
    Args:
        storage_path: Path in storage bucket
        expires_in: URL validity in seconds (default 1 hour)
        
    Returns:
        Signed URL or None if error
    """
    try:
        response = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
            path=storage_path,
            expires_in=expires_in
        )
        return response.get('signedURL')
    except Exception as e:
        logger.error(f"Error creating signed URL: {e}")
        return None
    
    
    