from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.sql import func
from database import Base

class Video(Base):
    """
    Video model - represents 'videos' table in database
    Each attribute = column in table
    """
    __tablename__ = "videos"  # Table name in database

    # Columns
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    duration = Column(Integer, nullable=False)  # in seconds
    file_size_mb = Column(Integer, nullable=True)
    status = Column(
        String(50), 
        nullable=False, 
        default="processing",
        index=True  # Index for faster queries by status
    )
    storage_url = Column(Text, nullable=True)
    
    # Timestamps - automatically managed
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),  # Auto-set on creation
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),  # Auto-update on changes
        nullable=False
    )

    def __repr__(self):
        """String representation for debugging"""
        return f"<Video(id={self.id}, title='{self.title}', status='{self.status}')>"


class Transcript(Base):
    """
    Transcript model - stores transcription segments
    Linked to Video via foreign key
    """
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, nullable=False, index=True)  # Links to videos.id
    full_text = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    word_count = Column(Integer, nullable=True)
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self):
        return f"<Transcript(id={self.id}, video_id={self.video_id}, words={self.word_count})>"