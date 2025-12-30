from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import sys
import logging

from database import get_db, engine
import models
import crud

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import storage and file utils (may fail if not configured)
try:
    from storage import upload_to_storage, is_video_file, get_file_type, get_signed_url
    STORAGE_AVAILABLE = True
    logger.info("Storage module loaded successfully")
except Exception as e:
    logger.error(f"Storage module failed to load: {e}")
    STORAGE_AVAILABLE = False

try:
    from file_utils import (
        generate_unique_filename, 
        sanitize_filename,
        validate_file_size,
        format_file_size,
        save_upload_file_tmp
    )
    FILE_UTILS_AVAILABLE = True
    logger.info("File utils loaded successfully")
except Exception as e:
    logger.error(f"File utils failed to load: {e}")
    FILE_UTILS_AVAILABLE = False

# Create database tables
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
except Exception as e:
    logger.error(f"Failed to create database tables: {e}")

# Create FastAPI app
app = FastAPI(
    title="StreamScribe API",
    description="""
AI-powered video transcription platform with cloud storage.

## Features
* Upload video files to cloud storage
* Automatic metadata extraction
* Secure file access with signed URLs
* Real-time transcription (coming soon)
* Semantic search (coming soon)

## File Upload
* Supported formats: MP4, MOV, AVI, MKV, WebM
* Maximum file size: 50MB
* Automatic video metadata extraction
    """,
    version="3.0.0",
    contact={
        "name": "Your Name",
        "email": "your.email@example.com"
    }
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas
from pydantic import BaseModel

class VideoBase(BaseModel):
    title: str
    duration: Optional[int] = None
    file_size_mb: Optional[int] = None

class VideoCreate(VideoBase):
    pass

class VideoResponse(VideoBase):
    id: int
    status: str
    storage_url: Optional[str] = None
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "service": "StreamScribe API",
        "version": "3.0.0",
        "status": "operational",
        "database": "PostgreSQL (Supabase)",
        "storage": "Supabase Storage" if STORAGE_AVAILABLE else "Not configured",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "videos": "/api/videos",
            "upload": "/api/videos/upload",
            "stats": "/api/stats"
        }
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    storage_status = "configured" if os.getenv("SUPABASE_URL") else "not configured"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "storage": storage_status,
        "storage_available": STORAGE_AVAILABLE,
        "file_utils_available": FILE_UTILS_AVAILABLE
    }


@app.get("/api/videos", response_model=List[VideoResponse])
def list_videos(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of videos
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum records to return
    - **status**: Filter by status (optional)
    """
    videos = crud.get_videos(db, skip=skip, limit=limit, status=status)
    return videos


@app.get("/api/videos/{video_id}", response_model=VideoResponse)
def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get single video by ID"""
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@app.post("/api/videos", response_model=VideoResponse, status_code=201)
def create_video(video: VideoCreate, db: Session = Depends(get_db)):
    """
    Create new video record (without file upload)
    For file upload, use /api/videos/upload endpoint
    """
    db_video = crud.create_video(
        db,
        title=video.title,
        duration=video.duration or 0,
        file_size_mb=video.file_size_mb
    )
    return db_video


@app.post("/api/videos/upload", status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload video file to storage and create database record
    
    - **file**: Video file to upload
    - **title**: Optional custom title (uses filename if not provided)
    """
    # Check if storage is available
    if not STORAGE_AVAILABLE or not FILE_UTILS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="File upload service not available. Storage not configured."
        )
    
    try:
        # Validate file is present
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Sanitize original filename
        original_filename = sanitize_filename(file.filename)
        
        # Use provided title or default to filename
        video_title = title if title else os.path.splitext(original_filename)[0]
        
        # Read file data
        file_data = await file.read()
        file_size_bytes = len(file_data)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Validate file size
        is_valid, error_msg = validate_file_size(file_size_bytes)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Detect file type
        mime_type = get_file_type(file_data[:2048])
        
        # Validate it's a video file
        if not is_video_file(mime_type):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {mime_type}. Only video files allowed."
            )
        
        # Generate unique filename
        unique_filename = generate_unique_filename(original_filename)
        
        # Upload to Supabase Storage
        upload_result = await upload_to_storage(
            file_data=file_data,
            filename=unique_filename,
            folder="uploads"
        )
        
        if not upload_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file: {upload_result.get('error')}"
            )
        
        # Create database record
        db_video = models.Video(
            title=video_title,
            duration=None,  # Could extract with ffmpeg later
            file_size_mb=int(file_size_mb),
            status="ready",
            storage_path=upload_result["storage_path"],
            storage_url=upload_result["file_url"],
            original_filename=original_filename,
            mime_type=mime_type
        )
        
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        logger.info(f"Video uploaded successfully: {db_video.id}")
        
        return {
            "message": "File uploaded successfully",
            "video": {
                "id": db_video.id,
                "title": db_video.title,
                "filename": original_filename,
                "size": format_file_size(file_size_bytes),
                "size_mb": int(file_size_mb),
                "mime_type": mime_type,
                "status": db_video.status,
                "storage_url": db_video.storage_url
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.delete("/api/videos/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    """Delete video from database and storage"""
    # Get video first
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Try to delete from storage
    if STORAGE_AVAILABLE and video.storage_path:
        try:
            from storage import delete_from_storage
            deleted = await delete_from_storage(video.storage_path)
            if deleted:
                logger.info(f"Deleted file from storage: {video.storage_path}")
        except Exception as e:
            logger.warning(f"Failed to delete from storage: {e}")
    
    # Delete from database
    success = crud.delete_video(db, video_id)
    if not success:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return {"message": f"Video {video_id} deleted successfully"}


@app.get("/api/videos/{video_id}/download")
async def download_video(video_id: int, db: Session = Depends(get_db)):
    """
    Get download URL for video
    Returns a signed URL valid for 1 hour
    """
    if not STORAGE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Storage service not available")
    
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not video.storage_path:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Generate signed URL (valid for 1 hour)
    signed_url = get_signed_url(video.storage_path, expires_in=3600)
    
    if not signed_url:
        raise HTTPException(status_code=500, detail="Failed to generate download URL")
    
    return {
        "download_url": signed_url,
        "filename": video.original_filename,
        "expires_in": 3600,
        "note": "URL expires in 1 hour"
    }


@app.get("/api/videos/{video_id}/stream")
async def stream_video(video_id: int, db: Session = Depends(get_db)):
    """
    Get streaming URL for video
    Returns a signed URL valid for 4 hours
    """
    if not STORAGE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Storage service not available")
    
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not video.storage_path:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Generate signed URL (valid for 4 hours for streaming)
    stream_url = get_signed_url(video.storage_path, expires_in=14400)
    
    if not stream_url:
        raise HTTPException(status_code=500, detail="Failed to generate stream URL")
    
    return {
        "stream_url": stream_url,
        "mime_type": video.mime_type,
        "title": video.title,
        "expires_in": 14400
    }


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Platform statistics
    """
    videos = crud.get_videos(db, limit=10000)
    total_duration = sum(v.duration or 0 for v in videos)
    total_size = sum(v.file_size_mb or 0 for v in videos)
    status_counts = crud.get_video_count_by_status(db)
    
    return {
        "total_videos": len(videos),
        "total_duration_hours": round(total_duration / 3600, 2) if total_duration else 0,
        "total_storage_gb": round(total_size / 1024, 2),
        "status_breakdown": status_counts,
        "database": "PostgreSQL",
        "storage_configured": STORAGE_AVAILABLE
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"detail": "Not Found"}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"detail": "Internal Server Error"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)