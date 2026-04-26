from fastapi import FastAPI, Depends, HTTPException, Security, Request, status
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import os

from . import models, schemas, crud
from .database import engine, get_db, SessionLocal
from .search import router as search_router

# Create all tables (In production, use Alembic migrations instead)
# Since we can't test Docker locally right now, we'll keep this disabled unless explicitly called
# models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CentralMemory API", 
    version="0.1.0",
    description="Centralized memory platform for multiple AI agents."
)

app.include_router(search_router)

from .deps import get_current_scopes, get_api_key_record, _hash_key

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/memories") or request.url.path.startswith("/entities") or request.url.path.startswith("/review-items") or request.url.path.startswith("/api-keys"):
        db = SessionLocal()
        try:
            raw_key = request.headers.get("X-API-Key", "")
            if not raw_key:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    raw_key = auth_header[7:]
            api_key_record = None
            if raw_key:
                hashed = _hash_key(raw_key)
                api_key_record = db.query(models.APIKey).filter(models.APIKey.hashed_key == hashed, models.APIKey.active == True).first()

            log = models.AuditLog(
                api_key_id=api_key_record.id if api_key_record else None,
                route=request.url.path,
                scope=None,
                action=f"{request.method} {response.status_code}"
            )
            db.add(log)
            db.commit()
        except Exception:
            pass
        finally:
            db.close()
    return response

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify API and DB connection."""
    from sqlalchemy import text
    try:
        # Check DB connection
        db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "CentralMemory API is running and connected to DB."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/openapi_trimmed.json")
def get_trimmed_spec():
    spec_path = os.path.join(os.path.dirname(__file__), "openapi_trimmed.json")
    return FileResponse(spec_path, media_type="application/json")

# --- Memories Endpoints ---

@app.post("/memories", response_model=schemas.MemoryResponse, status_code=status.HTTP_201_CREATED)
def create_memory(
    memory: schemas.MemoryCreate, 
    db: Session = Depends(get_db), 
    scopes: List[str] = Depends(get_current_scopes)
):
    """
    Accepts payload, writes `memories` + `ingestion_jobs` in one transaction.
    Worker performs chunking/embedding asynchronously.
    """
    # Scope validation
    if memory.scope not in scopes and "admin" not in scopes:
        raise HTTPException(status_code=403, detail=f"API Key does not have permission to write to scope: {memory.scope}")

    # All non-human clients default to 'scratch' in v1
    # We will let admin UI pass a custom initial status if required later, but standard create is scratch.
    db_memory, db_job = crud.create_memory(db=db, memory=memory, initial_status="scratch")
    
    if db_job is None:
        # Exact duplicate found
        # In a real app we might return 409 Conflict or 200 OK. Returning 200 with existing object.
        pass
        
    return db_memory

@app.get("/memories", response_model=List[schemas.MemoryResponse])
def get_memories(
    skip: int = 0, 
    limit: int = 10, 
    include_scratch: bool = False,
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    """List recent memory."""
    return crud.get_memories(db=db, skip=skip, limit=limit, include_scratch=include_scratch, scopes=scopes)

@app.get("/memories/{memory_id}", response_model=schemas.MemoryResponse)
def get_memory(
    memory_id: UUID, 
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    """Fetch memory by ID."""
    db_memory = crud.get_memory(db=db, memory_id=memory_id)
    if db_memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    if db_memory.scope not in scopes and "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    return db_memory

@app.patch("/memories/{memory_id}", response_model=schemas.MemoryResponse)
def update_memory(
    memory_id: UUID, 
    memory_update: schemas.MemoryUpdate,
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    """Update memory by ID (including promotion)."""
    db_memory = crud.get_memory(db=db, memory_id=memory_id)
    if db_memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    if db_memory.scope not in scopes and "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    if memory_update.status and memory_update.status not in ["scratch"] and "admin" not in scopes:
         raise HTTPException(status_code=403, detail="Only admins can promote status beyond scratch")
         
    return crud.update_memory(db=db, memory_id=memory_id, memory_update=memory_update)

@app.post("/memories/{memory_id}/archive", response_model=schemas.MemoryResponse)
def archive_memory(
    memory_id: UUID, 
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    """Soft delete memory."""
    db_memory = crud.archive_memory(db=db, memory_id=memory_id)
    if db_memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return db_memory

@app.delete("/memories/{memory_id}/purge", status_code=status.HTTP_204_NO_CONTENT)
def purge_memory(
    memory_id: UUID, 
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    """Hard delete for sensitive data spills (Admin only)."""
    if "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Admin scope required to purge memory")
        
    success = crud.purge_memory(db=db, memory_id=memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return None

# --- Entities Endpoints ---

@app.post("/entities", response_model=schemas.EntityResponse, status_code=status.HTTP_201_CREATED)
def create_entity(
    entity: schemas.EntityCreate, 
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    return crud.create_entity(db=db, entity=entity)

@app.get("/entities", response_model=List[schemas.EntityResponse])
def get_entities(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    return crud.get_entities(db=db, skip=skip, limit=limit)

# --- Review Items Endpoints ---

@app.get("/review-items", response_model=List[schemas.ReviewItemResponse])
def get_review_items(
    skip: int = 0, 
    limit: int = 100, 
    status: str = "pending",
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    if "admin" not in scopes:
         raise HTTPException(status_code=403, detail="Admin scope required")
    return crud.get_review_items(db=db, skip=skip, limit=limit, status=status)

@app.post("/review-items/{item_id}/resolve", response_model=schemas.ReviewItemResponse)
def resolve_review_item(
    item_id: UUID, 
    resolution: schemas.ReviewItemResolve,
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    if "admin" not in scopes:
         raise HTTPException(status_code=403, detail="Admin scope required")
         
    db_item = crud.resolve_review_item(db=db, item_id=item_id, resolution=resolution)
    if not db_item:
         raise HTTPException(status_code=404, detail="Review item not found")
         
    return db_item

# --- Stats Endpoint ---

@app.get("/stats", response_model=schemas.MemoryStatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    if "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Admin scope required")
    return crud.get_memory_stats(db=db)

# --- Ingestion Jobs Endpoints ---

@app.get("/ingestion-jobs", response_model=List[schemas.IngestionJobResponse])
def get_ingestion_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    if "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Admin scope required")
    return crud.get_ingestion_jobs(db=db, skip=skip, limit=limit, status=status)

@app.post("/ingestion-jobs/{job_id}/retry", response_model=schemas.IngestionJobResponse)
def retry_ingestion_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    if "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Admin scope required")
    db_job = crud.retry_ingestion_job(db=db, job_id=job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

# --- API Key Endpoints ---

@app.get("/api-keys", response_model=List[schemas.APIKeyResponse])
def get_api_keys(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    if "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Admin scope required")
    return crud.get_api_keys(db=db, skip=skip, limit=limit)

@app.post("/api-keys", response_model=schemas.APIKeyCreateResponse)
def create_api_key(
    key_data: schemas.APIKeyCreate,
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    if "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Admin scope required")
    db_key, plain_key = crud.create_api_key(db=db, key_data=key_data)
    return schemas.APIKeyCreateResponse(
        id=db_key.id,
        name=db_key.name,
        allowed_scopes=db_key.allowed_scopes,
        can_read=db_key.can_read,
        can_write=db_key.can_write,
        active=db_key.active,
        last_used_at=db_key.last_used_at,
        created_at=db_key.created_at,
        plain_key=plain_key
    )

@app.post("/api-keys/{key_id}/revoke", response_model=schemas.APIKeyResponse)
def revoke_api_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    if "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Admin scope required")
    db_key = crud.revoke_api_key(db=db, key_id=key_id)
    if not db_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    return db_key

# --- Audit Log Endpoints ---

@app.get("/audit-logs", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    if "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Admin scope required")
    return crud.get_audit_logs(db=db, skip=skip, limit=limit)

@app.post("/reindex", response_model=schemas.BulkReindexResponse)
def bulk_reindex(
    status: Optional[str] = None,
    scope: Optional[str] = None,
    force: bool = False,
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    if "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Admin scope required")
    result = crud.bulk_reindex(db=db, status_filter=status, scope_filter=scope, force=force)
    return schemas.BulkReindexResponse(
        queued=result["queued"],
        skipped_no_content=result["skipped_no_content"],
        message=f"Queued {result['queued']} memories for re-embedding"
    )
