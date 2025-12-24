from database import SessionLocal
import crud

def seed_database():
    """Add initial data to database for testing"""
    db = SessionLocal()
    
    try:
        # Sample videos
        videos_data = [
            {
                "title": "Introduction to Machine Learning",
                "duration": 1800,
                "file_size_mb": 450
            },
            {
                "title": "FastAPI Production Guide",
                "duration": 2400,
                "file_size_mb": 600
            },
            {
                "title": "PostgreSQL Best Practices",
                "duration": 3000,
                "file_size_mb": 750
            },
            {
                "title": "Docker Deployment Tutorial",
                "duration": 1500,
                "file_size_mb": 380
            }
        ]
        
        print("Seeding database...")
        
        for video_data in videos_data:
            video = crud.create_video(
                db,
                title=video_data["title"],
                duration=video_data["duration"],
                file_size_mb=video_data["file_size_mb"]
            )
            print(f"✓ Created: {video.title}")
        
        # Update one to "ready" status
        crud.update_video_status(db, 1, "ready")
        print("✓ Updated video 1 status to 'ready'")
        
        print(f"\n✓ Successfully seeded {len(videos_data)} videos!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()