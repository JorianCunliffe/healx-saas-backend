
import logging
import sys
import os

# Configure logging immediately to catch startup errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("app.main")
logger.info("Initializing HealX Backend...")

from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uvicorn

from app.database import get_db, engine, Base
from app.auth.dependencies import get_current_user_id
from app.services.ingestion import IngestionService
from app.services.media import MediaService
from app.schemas import (
    BatchIngestRequest, JournalEntryCreate, MediaUploadRequest, ObservationResponse
)
from app.models import User, JournalEntry, MediaFile

app = FastAPI(title="HealX Health Data Vault")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    logger.info("Application startup event triggered.")
    try:
        # Create tables (SQLite fallback or Postgres)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"CRITICAL DATABASE ERROR: Could not connect to DB. App running in limited mode. Error: {e}")

# --- FRONTEND SERVING ---
# Serve the React app directly from the FastAPI backend for simple deployment

@app.get("/")
async def serve_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "HealX Backend Running. index.html not found."}

@app.get("/index.tsx")
async def serve_tsx():
    if os.path.exists("index.tsx"):
        return FileResponse("index.tsx", media_type="text/plain")
    return {"error": "File not found"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "HealX Backend"}

# --- OBSERVATIONS ---

@app.post("/observations/batch", status_code=201)
async def ingest_batch(
    payload: BatchIngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # Quick mock check for test harness dummy user
    if user_id.startswith("user-uuid-"):
        pass 

    service = IngestionService(db)
    result = await service.process_batch(user_id, payload)
    
    return {"status": "success", "details": result}

# --- JOURNAL ---

@app.post("/journal", status_code=201)
async def save_journal_entry(
    entry: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    new_entry = JournalEntry(
        user_id=user_id,
        entry_date=entry.entry_date,
        content_markdown=entry.content,
        mood_score=entry.mood_score,
        tags=entry.tags
    )
    db.add(new_entry)
    await db.commit()
    return {"status": "saved", "id": str(new_entry.id)}

# --- MEDIA ---

@app.post("/media/upload-url")
async def get_presigned_url(
    req: MediaUploadRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = MediaService.generate_signed_url(user_id, req.filename, req.content_type)
    
    media_file = MediaFile(
        user_id=user_id,
        category=req.file_type,
        s3_bucket=os.getenv('FIREBASE_STORAGE_BUCKET', 'unknown'),
        s3_key=result['file_path'],
        filename=req.filename,
        mime_type=req.content_type
    )
    db.add(media_file)
    await db.commit()
    
    return result

if __name__ == "__main__":
    # Cloud Run provides PORT via env var
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting Uvicorn on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
