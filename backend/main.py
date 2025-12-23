from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(
    title="StreamScribe API",
    description="AI-powered video transcription platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoBase(BaseModel):
    title: str
    duration: int
    file_size_mb: Optional[int] = None

class Video(VideoBase):
    id: int
    status: str
    created_at: str

videos_db = [
    {
        "id": 1,
        "title": "Introduction to Machine Learning",
        "duration": 1200,
        "file_size_mb": 450,
        "status": "ready",
        "created_at": "2025-12-19T10:00:00"
    },
    {
        "id": 2,
        "title": "FastAPI Tutorial",
        "duration": 1800,
        "file_size_mb": 600,
        "status": "processing",
        "created_at": "2025-12-19T11:30:00"
    }
]

@app.get("/")
def root():
    return {
        "service": "StreamScribe API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/videos", response_model=List[Video])
def list_videos():
    return videos_db

@app.get("/api/videos/{video_id}", response_model=Video)
def get_video(video_id: int):
    video = next((v for v in videos_db if v["id"] == video_id), None)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@app.post("/api/videos", response_model=Video)
def create_video(video: VideoBase):
    new_video = {
        "id": len(videos_db) + 1,
        "title": video.title,
        "duration": video.duration,
        "file_size_mb": video.file_size_mb,
        "status": "processing",
        "created_at": datetime.now().isoformat()
    }
    videos_db.append(new_video)
    return new_video

@app.delete("/api/videos/{video_id}")
def delete_video(video_id: int):
    global videos_db
    original_length = len(videos_db)
    videos_db = [v for v in videos_db if v["id"] != video_id]
    if len(videos_db) == original_length:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"message": f"Video {video_id} deleted"}

@app.get("/api/stats")
def get_stats():
    total_duration = sum(v["duration"] for v in videos_db)
    total_size = sum(v.get("file_size_mb", 0) for v in videos_db)
    return {
        "total_videos": len(videos_db),
        "total_duration_hours": round(total_duration / 3600, 2),
        "total_storage_gb": round(total_size / 1024, 2),
        "status_breakdown": {
            "ready": len([v for v in videos_db if v["status"] == "ready"]),
            "processing": len([v for v in videos_db if v["status"] == "processing"])
        }
    }