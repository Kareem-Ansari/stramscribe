from sqlalchemy.orm import Session
from typing import List, Optional
import models
from pydantic import BaseModel

from sqlalchemy.exc import SQLAlchemyError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CRUD = Create, Read, Update, Delete
# These functions handle all database operations

def get_video(db: Session, video_id: int) -> Optional[models.Video]:
    """
    Get single video by ID
    
    Args:
        db: Database session
        video_id: ID of video to get
        
    Returns:
        Video object or None if not found
    """
    return db.query(models.Video).filter(models.Video.id == video_id).first()


def get_videos(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None
) -> List[models.Video]:
    """
    Get list of videos with optional filtering
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        status: Optional status filter
        
    Returns:
        List of Video objects
    """
    query = db.query(models.Video)
    
    # Apply status filter if provided
    if status:
        query = query.filter(models.Video.status == status)
    
    # Apply pagination and return
    return query.offset(skip).limit(limit).all()


def create_video(db: Session, title: str, duration: int, file_size_mb: Optional[int] = None) -> models.Video:
    """
    Create new video with error handling
    """
    try:
        # Validate inputs
        if duration <= 0:
            raise ValueError("Duration must be positive")
        
        if len(title.strip()) == 0:
            raise ValueError("Title cannot be empty")
        
        # Create video
        db_video = models.Video(
            title=title.strip(),  # Remove whitespace
            duration=duration,
            file_size_mb=file_size_mb,
            status="processing"
        )
        
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        logger.info(f"Created video: {db_video.id} - {db_video.title}")
        return db_video
        
    except SQLAlchemyError as e:
        logger.error(f"Database error creating video: {e}")
        db.rollback()
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise


def update_video_status(db: Session, video_id: int, status: str) -> Optional[models.Video]:
    """
    Update video status
    
    Args:
        db: Database session
        video_id: ID of video to update
        status: New status value
        
    Returns:
        Updated Video object or None if not found
    """
    db_video = get_video(db, video_id)
    
    if db_video:
        db_video.status = status
        db.commit()
        db.refresh(db_video)
    
    return db_video


def delete_video(db: Session, video_id: int) -> bool:
    """
    Delete video from database
    
    Args:
        db: Database session
        video_id: ID of video to delete
        
    Returns:
        True if deleted, False if not found
    """
    db_video = get_video(db, video_id)
    
    if db_video:
        db.delete(db_video)
        db.commit()
        return True
    
    return False


def get_video_count_by_status(db: Session) -> dict:
    """
    Get count of videos grouped by status
    
    Returns:
        Dictionary with status counts
    """
    from sqlalchemy import func
    
    results = (
        db.query(models.Video.status, func.count(models.Video.id))
        .group_by(models.Video.status)
        .all()
    )
    
    return {status: count for status, count in results}