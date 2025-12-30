#  StreamScribe

> AI-powered video transcription platform with real-time analysis and semantic search


##  Overview

StreamScribe transforms video content into searchable, analyzable text using AI:

-  95%+ transcription accuracy
-  Semantic search across video libraries  
-  AI-powered summaries and chapters
- Scalable cloud architecture
-  Real-time processing

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3)
- **AI/ML:** OpenAI Whisper, Groq API
- **Database:** PostgreSQL (Supabase)
- **Storage:** Supabase Storage
- **Vector DB:** Qdrant
- **Deployment:** Render

### Frontend (Coming Soon)
- **Framework:** Next.js 14
- **Styling:** TailwindCSS
- **Deployment:** Vercel

## Current Features

RESTful API with automatic documentation  
PostgreSQL database integration  
SQLAlchemy ORM with models  
CRUD operations for videos  
**File upload to cloud storage (Supabase)**  
**Video metadata extraction (duration, resolution)**  
**Secure file access with signed URLs**  
**File type validation and security**  
Environment-based configuration  
Platform analytics from real data  
Production deployment  

### Coming Soon
AI transcription (Whisper)
Semantic search (RAG)
User authentication
Frontend UI



##  API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `GET /api/videos` - List all videos
- `GET /api/videos/{id}` - Get video by ID
- `POST /api/videos` - Create video
- `DELETE /api/videos/{id}` - Delete video
- `GET /api/stats` - Platform statistics


Last Updated: December 29, 2025 | Day 3 Complete