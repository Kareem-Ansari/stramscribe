from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")


# Create database engine
# Engine = manages connections to database
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,         # Keep 5 connections ready
    max_overflow=10      # Allow 10 extra connections if needed
)

# Create session factory
# Session = your "conversation" with database
SessionLocal = sessionmaker(
    autocommit=False,    # Don't auto-save changes
    autoflush=False,     # Don't auto-send to database
    bind=engine          # Connect to our engine
)

# Base class for our models
# All database tables will inherit from this
Base = declarative_base()

# Dependency to get database session
def get_db():
    """
    Provides a database session to route handlers.
    Automatically closes session when done.
    This is called 'dependency injection'
    """
    db = SessionLocal()  # Create new session
    try:
        yield db  # Give session to route
    finally:
        db.close()  # Always close when done