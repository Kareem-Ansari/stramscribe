from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os

from database import get_db, engine
import models
import crud
from storage import upload_to_storage, is_video_file, get_file_type
from file_utils import (
    generate_unique_filename, 
    sanitize_filename,
    validate_file_size,
    format_file_size
)

# Create database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="StreamScribe API",
    description="AI-powered video transcription platform with real database",
    version="2.0.0"  # Updated version!
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
from pydantic import BaseModel

class VideoBase(BaseModel):
    title: str
    duration: int
    file_size_mb: Optional[int] = None

class VideoCreate(VideoBase):
    pass

class VideoResponse(VideoBase):
    id: int
    status: str
    storage_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# API Endpoints - Now using real database!

@app.get("/")
def root():
    return {
        "service": "StreamScribe API",
        "version": "2.0.0",
        "status": "operational",
        "database": "PostgreSQL (Supabase)",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "videos": "/api/videos"
        }
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check - now verifies database connection!
    Notice the Depends(get_db) - this is dependency injection
    """
    try:
        # Try a simple query to verify database connection
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status
    }

@app.get("/api/videos", response_model=List[VideoResponse])
def list_videos(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of videos from database
    
    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Max records to return
    - status: Filter by status (optional)
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
    Create new video
    Now saves to real database!
    """
    db_video = crud.create_video(
        db,
        title=video.title,
        duration=video.duration,
        file_size_mb=video.file_size_mb
    )
    return db_video

@app.delete("/api/videos/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    """Delete video from database"""
    success = crud.delete_video(db, video_id)
    if not success:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"message": f"Video {video_id} deleted successfully"}

@app.patch("/api/videos/{video_id}/status")
def update_status(
    video_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Update video status"""
    video = crud.update_video_status(db, video_id, status)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"message": "Status updated", "video": video}

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Platform statistics from database
    """
    # Get all videos
    videos = crud.get_videos(db, limit=10000)
    
    # Calculate stats
    total_duration = sum(v.duration for v in videos)
    total_size = sum(v.file_size_mb or 0 for v in videos)
    
    # Get status breakdown
    status_counts = crud.get_video_count_by_status(db)
    
    return {
        "total_videos": len(videos),
        "total_duration_hours": round(total_duration / 3600, 2),
        "total_storage_gb": round(total_size / 1024, 2),
        "status_breakdown": status_counts,
        "database": "PostgreSQL"
    }
    
    
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
        validate_upload_request(original_filename, video_title, file_size_bytes)
        file_size_mb = file_size_bytes / (1024 * 1024)
        from validators import validate_upload_request

        
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
            duration=None,  # Will extract later with ffmpeg
            file_size_mb=int(file_size_mb),
            status="processing",
            storage_path=upload_result["storage_path"],
            storage_url=upload_result["file_url"],
            original_filename=original_filename,
            mime_type=mime_type
        )
        
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
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
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
from fastapi.responses import StreamingResponse
import io

@app.get("/api/videos/{video_id}/download")
async def download_video(video_id: int, db: Session = Depends(get_db)):
    """
    Download video file
    Generates signed URL for secure download
    """
    # Get video from database
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not video.storage_path:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Generate signed URL (valid for 1 hour)
    from storage import get_signed_url
    
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
    Stream video for playback
    Returns signed URL for streaming
    """
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not video.storage_path:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Generate signed URL (valid for 4 hours for streaming)
    from storage import get_signed_url
    
    stream_url = get_signed_url(video.storage_path, expires_in=14400)
    
    return {
        "stream_url": stream_url,
        "mime_type": video.mime_type,
        "title": video.title
    }
    
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
    * Maximum file size: 100MB
    * Automatic video metadata extraction
    """,
    version="3.0.0",
    contact={
        "name": "Your Name",
        "email": "your.email@example.com"
    }
)