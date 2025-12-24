from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

# Import our new modules
from database import get_db, engine
import models
import crud

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