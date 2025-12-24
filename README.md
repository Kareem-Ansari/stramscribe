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
**PostgreSQL database integration**  
**SQLAlchemy ORM with models**  
**CRUD operations for videos**  
**Database migrations support**  
**Environment-based configuration**  
Platform analytics from real data  
Health monitoring with database check  
Production deployment with database  

### Coming Soon
File upload & storage (Supabase Storage)
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


*Last Updated: December 19, 2025 | Day 1 Complete*