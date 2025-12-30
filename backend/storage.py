from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional
import logging

# DEBUG: Print environment variables (REMOVE IN PRODUCTION)
print(f"DEBUG - SUPABASE_URL: {SUPABASE_URL}")
print(f"DEBUG - SUPABASE_KEY: {'SET' if SUPABASE_KEY else 'NOT SET'}")
print(f"DEBUG - SUPABASE_BUCKET: {SUPABASE_BUCKET}")

# Load environment variables (works locally, not on Render)
load_dotenv()

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "videos")

# Only create client if credentials are available
supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        supabase = None
else:
    logger.warning("Supabase credentials not found. File upload will not work.")


def get_file_type(file_data: bytes) -> str:
    """Detect file type from binary data"""
    try:
        # Simple detection without python-magic dependency
        if file_data[:4] == b'\x00\x00\x00\x18' or file_data[:4] == b'\x00\x00\x00\x1c':
            return "video/mp4"
        elif file_data[:4] == b'RIFF':
            return "video/avi"
        elif file_data[:8] == b'\x00\x00\x00\x14ftypqt':
            return "video/quicktime"
        else:
            return "video/mp4"  # Default to mp4
    except Exception as e:
        logger.error(f"Error detecting file type: {e}")
        return "video/mp4"


def is_video_file(mime_type: str) -> bool:
    """Check if MIME type is a video"""
    allowed_types = [
        'video/mp4',
        'video/quicktime',
        'video/x-msvideo',
        'video/x-matroska',
        'video/webm'
    ]
    return mime_type in allowed_types


async def upload_to_storage(
    file_data: bytes,
    filename: str,
    folder: str = "uploads"
) -> dict:
    """Upload file to Supabase Storage"""
    
    # Check if Supabase client is available
    if not supabase:
        logger.error("Supabase client not initialized")
        return {
            "success": False,
            "error": "Storage service not configured"
        }
    
    try:
        storage_path = f"{folder}/{filename}"
        mime_type = get_file_type(file_data[:2048])
        
        # Upload to Supabase Storage
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file_data,
            file_options={
                "content-type": mime_type,
                "upsert": "true"
            }
        )
        
        # Get public URL
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)
        
        logger.info(f"File uploaded successfully: {storage_path}")
        
        return {
            "success": True,
            "storage_path": storage_path,
            "file_url": public_url,
            "mime_type": mime_type
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def delete_from_storage(storage_path: str) -> bool:
    """Delete file from Supabase Storage"""
    if not supabase:
        return False
    
    try:
        supabase.storage.from_(SUPABASE_BUCKET).remove([storage_path])
        logger.info(f"File deleted: {storage_path}")
        return True
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return False


def get_signed_url(storage_path: str, expires_in: int = 3600) -> Optional[str]:
    """Generate signed URL for private file access"""
    if not supabase:
        return None
    
    try:
        response = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
            path=storage_path,
            expires_in=expires_in
        )
        return response.get('signedURL')
    except Exception as e:
        logger.error(f"Error creating signed URL: {e}")
        return None