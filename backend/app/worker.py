import os
import re
import signal
import time
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from .database import SessionLocal, engine
from .models import IngestionJob, Memory, MemoryChunk

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_MODEL_VERSION = os.getenv("EMBEDDING_MODEL_VERSION", "latest")

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
MIN_CHUNK_SIZE = 100

_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+|\n{2,}')

def _split_sentences(text: str) -> List[str]:
    parts = _SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    sentences = _split_sentences(text)
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for sentence in sentences:
        sent_len = len(sentence)
        if current_len + sent_len + 1 > chunk_size and current:
            chunks.append(" ".join(current))
            overlap_text = " ".join(current)
            while len(overlap_text) > overlap and current:
                overlap_text = overlap_text[len(current[0]) + 1:]
                current.pop(0)
            current_len = len(overlap_text)
        current.append(sentence)
        current_len += sent_len + 1

    if current:
        last = " ".join(current)
        if chunks and len(last) < MIN_CHUNK_SIZE:
            chunks[-1] = chunks[-1] + " " + last
        else:
            chunks.append(last)

    return chunks


def simple_chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    return chunk_text(text, chunk_size, overlap)

def generate_embedding(text: str) -> List[float]:
    """Calls Ollama to generate an embedding for the given text."""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("embedding", [])
    except Exception as e:
        print(f"Error calling Ollama API: {e}")
        raise

def process_ingestion_job(db: Session, job: IngestionJob):
    """Processes a single pending ingestion job."""
    print(f"Processing Job {job.id} for Memory {job.memory_id}...")
    
    # Mark as running
    job.status = "running"
    job.started_at = text("CURRENT_TIMESTAMP")
    job.attempt_count += 1
    db.commit()
    
    try:
        # Fetch associated memory
        memory = db.query(Memory).filter(Memory.id == job.memory_id).first()
        if not memory:
            raise ValueError(f"Memory {job.memory_id} not found.")

        # Delete any existing chunks for this memory to allow re-embedding
        db.query(MemoryChunk).filter(MemoryChunk.memory_id == memory.id).delete()
        
        # Chunk text
        chunks = simple_chunk_text(memory.content)
        
        # Embed and save
        for idx, chunk_content in enumerate(chunks):
            embedding = generate_embedding(chunk_content)
            
            db_chunk = MemoryChunk(
                memory_id=memory.id,
                chunk_index=idx,
                content=chunk_content,
                embedding=embedding,
                embedding_model=EMBEDDING_MODEL,
                embedding_model_version=EMBEDDING_MODEL_VERSION
            )
            db.add(db_chunk)
            
        # Complete Job
        job.status = "completed"
        job.completed_at = text("CURRENT_TIMESTAMP")
        db.commit()
        print(f"Job {job.id} completed successfully.")

    except Exception as e:
        print(f"Job {job.id} failed: {e}")
        db.rollback()
        # Reload job in a new session because of rollback
        job_reload = db.query(IngestionJob).filter(IngestionJob.id == job.id).first()
        job_reload.status = "failed"
        job_reload.last_error = str(e)
        db.commit()

def run_worker():
    """Polls the `ingestion_jobs` table for pending jobs and processes them."""
    global _shutdown
    print("Starting CentralMemory Background Worker...")
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    
    while not _shutdown:
        db = SessionLocal()
        try:
            job = db.query(IngestionJob).filter(IngestionJob.status == "pending").first()
            
            if job:
                process_ingestion_job(db, job)
            else:
                time.sleep(5)
                
        except Exception as e:
            print(f"Worker iteration error: {e}")
            time.sleep(5)
        finally:
            db.close()

    print("Worker shutting down, resetting running jobs...")
    db = SessionLocal()
    try:
        db.query(IngestionJob).filter(IngestionJob.status == "running").update({"status": "pending"})
        db.commit()
    except Exception as e:
        print(f"Error resetting jobs on shutdown: {e}")
    finally:
        db.close()
    print("Worker shutdown complete.")

_shutdown = False
def _handle_signal(signum, frame):
    global _shutdown
    _shutdown = True
    print(f"Received signal {signum}, shutting down gracefully...")

if __name__ == "__main__":
    run_worker()