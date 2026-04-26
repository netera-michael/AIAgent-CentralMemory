import hashlib
import json
import secrets
from datetime import datetime, timezone
from uuid import UUID
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, desc, func
from . import models, schemas

def get_memory(db: Session, memory_id: UUID) -> Optional[models.Memory]:
    return db.query(models.Memory).filter(models.Memory.id == memory_id).first()

def get_memories(db: Session, skip: int = 0, limit: int = 100, include_scratch: bool = False, scopes: List[str] = None) -> List[models.Memory]:
    query = db.query(models.Memory)
    
    # Filter by scope if provided (RBAC)
    if scopes and "public" not in scopes:
        query = query.filter(models.Memory.scope.in_(scopes))
        
    # Default search filters to reviewed and canonical unless scratch is explicitly requested
    if not include_scratch:
        query = query.filter(models.Memory.status.in_(["reviewed", "canonical"]))
        
    return query.order_by(desc(models.Memory.created_at)).offset(skip).limit(limit).all()

def update_memory(db: Session, memory_id: UUID, memory_update: schemas.MemoryUpdate) -> Optional[models.Memory]:
    db_memory = get_memory(db, memory_id)
    if not db_memory:
        return None
    
    update_data = memory_update.model_dump(exclude_unset=True)
    
    content_changed = "content" in update_data and update_data["content"] != db_memory.content
    invalidate = update_data.pop("invalidate_previous", True)
    
    now = datetime.now(timezone.utc)
    
    if content_changed and invalidate:
        old_hash = db_memory.content_hash
        archive_suffix = f":archived:{now.isoformat()}"
        old_memory = models.Memory(
            type=db_memory.type,
            title=db_memory.title,
            content=db_memory.content,
            content_hash=old_hash + archive_suffix,
            summary=db_memory.summary,
            scope=db_memory.scope,
            sensitivity=db_memory.sensitivity,
            status="archived",
            confidence=db_memory.confidence,
            source_id=db_memory.source_id,
            entity_id=db_memory.entity_id,
            canonical_group_id=db_memory.canonical_group_id,
            valid_from=db_memory.valid_from or db_memory.created_at,
            valid_until=now,
            archived_at=now,
            observed_at=db_memory.observed_at,
            _metadata=db_memory.metadata_
        )
        db.add(old_memory)
        db.flush()
        db_memory.supersedes_memory_id = old_memory.id
        db_memory.valid_from = now
    
    if "valid_until" in update_data and update_data["valid_until"] is not None:
        db_memory.valid_until = update_data.pop("valid_until")
    
    for key, value in update_data.items():
        if key == "content":
            db_memory.content = value
            db_memory.content_hash = calculate_content_hash(value)
        elif key not in ("invalidate_previous",):
            setattr(db_memory, key, value)
    
    if content_changed:
        db.query(models.MemoryChunk).filter(models.MemoryChunk.memory_id == memory_id).delete()
        db_job = models.IngestionJob(
            memory_id=memory_id,
            job_type="re_embed",
            status="pending",
            payload={"action": "chunk_and_embed"}
        )
        db.add(db_job)
        
    db.commit()
    db.refresh(db_memory)
    return db_memory

def calculate_content_hash(content: str) -> str:
    """Calculates SHA-256 hash for exact duplicate rejection."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def create_memory(db: Session, memory: schemas.MemoryCreate, initial_status: str = "scratch") -> tuple[models.Memory, Optional[models.IngestionJob]]:
    # Calculate hash and check for exact duplicates
    content_hash = calculate_content_hash(memory.content)
    
    existing = db.query(models.Memory).filter(models.Memory.content_hash == content_hash).first()
    if existing:
        return existing, None

    # Write memory to DB
    db_memory = models.Memory(
        type=memory.type,
        title=memory.title,
        content=memory.content,
        content_hash=content_hash,
        summary=memory.summary,
        scope=memory.scope,
        sensitivity=memory.sensitivity,
        status=initial_status,
        confidence=memory.confidence,
        source_id=memory.source_id,
        entity_id=memory.entity_id,
        canonical_group_id=memory.canonical_group_id,
        supersedes_memory_id=memory.supersedes_memory_id,
        valid_from=memory.valid_from or datetime.now(timezone.utc),
        valid_until=memory.valid_until,
        observed_at=memory.observed_at,
        _metadata=memory.metadata_
    )
    db.add(db_memory)
    db.flush()  # To get db_memory.id

    # Create ingestion job for async embedding/chunking
    db_job = models.IngestionJob(
        memory_id=db_memory.id,
        job_type="ingest_memory",
        status="pending",
        payload={"action": "chunk_and_embed"}
    )
    db.add(db_job)
    
    db.commit()
    db.refresh(db_memory)
    
    return db_memory, db_job

def archive_memory(db: Session, memory_id: UUID) -> Optional[models.Memory]:
    db_memory = get_memory(db, memory_id)
    if not db_memory:
        return None
        
    db_memory.status = "archived"
    db_memory.archived_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_memory)
    return db_memory

def purge_memory(db: Session, memory_id: UUID) -> bool:
    """Hard delete for sensitive data spills."""
    db_memory = get_memory(db, memory_id)
    if not db_memory:
        return False
        
    db.delete(db_memory)
    db.commit()
    return True

# Entities
def get_entity(db: Session, entity_id: UUID) -> Optional[models.Entity]:
    return db.query(models.Entity).filter(models.Entity.id == entity_id).first()

def get_entities(db: Session, skip: int = 0, limit: int = 100) -> List[models.Entity]:
    return db.query(models.Entity).offset(skip).limit(limit).all()

def create_entity(db: Session, entity: schemas.EntityCreate) -> models.Entity:
    normalized_name = entity.name.lower().strip()
    
    # Check if entity exists
    existing = db.query(models.Entity).filter(models.Entity.normalized_name == normalized_name).first()
    if existing:
        return existing

    db_entity = models.Entity(
        type=entity.type,
        name=entity.name,
        normalized_name=normalized_name,
        description=entity.description,
        _metadata=entity.metadata_
    )
    db.add(db_entity)
    db.commit()
    db.refresh(db_entity)
    return db_entity

# Review Items
def get_review_items(db: Session, skip: int = 0, limit: int = 100, status: str = "pending") -> List[models.ReviewItem]:
    return db.query(models.ReviewItem).filter(models.ReviewItem.status == status).order_by(desc(models.ReviewItem.created_at)).offset(skip).limit(limit).all()

def get_review_item(db: Session, item_id: UUID) -> Optional[models.ReviewItem]:
    return db.query(models.ReviewItem).filter(models.ReviewItem.id == item_id).first()

def resolve_review_item(db: Session, item_id: UUID, resolution: schemas.ReviewItemResolve) -> Optional[models.ReviewItem]:
    db_item = get_review_item(db, item_id)
    if not db_item:
        return None
        
    db_item.status = "resolved"
    db_item.resolved_at = datetime.now(timezone.utc)
    if resolution.resolution_notes:
        db_item.reason = f"{db_item.reason or ''} | Resolution: {resolution.resolution_notes}"
    
    # In a real system, the specific logic (merge, supersede, etc.) 
    # would execute here depending on `resolution.action`.
    # For v1 admin UI, the UI will often just resolve the item 
    # and perform the memory promotion via separate PUT/PATCH calls.
    
    db.commit()
    db.refresh(db_item)
    return db_item

# --- API Keys ---

def get_api_keys(db: Session, skip: int = 0, limit: int = 100) -> List[models.APIKey]:
    return db.query(models.APIKey).order_by(desc(models.APIKey.created_at)).offset(skip).limit(limit).all()

def create_api_key(db: Session, key_data: schemas.APIKeyCreate) -> tuple[models.APIKey, str]:
    plain_key = f"cm_{secrets.token_urlsafe(32)}"
    hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()

    db_key = models.APIKey(
        name=key_data.name,
        hashed_key=hashed_key,
        allowed_scopes=key_data.allowed_scopes,
        can_read=key_data.can_read,
        can_write=key_data.can_write,
        active=True
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key, plain_key

def revoke_api_key(db: Session, key_id: UUID) -> Optional[models.APIKey]:
    db_key = db.query(models.APIKey).filter(models.APIKey.id == key_id).first()
    if not db_key:
        return None
    db_key.active = False
    db.commit()
    db.refresh(db_key)
    return db_key

# --- Ingestion Jobs ---

def get_ingestion_jobs(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[models.IngestionJob]:
    query = db.query(models.IngestionJob)
    if status:
        query = query.filter(models.IngestionJob.status == status)
    return query.order_by(desc(models.IngestionJob.created_at)).offset(skip).limit(limit).all()

def retry_ingestion_job(db: Session, job_id: UUID) -> Optional[models.IngestionJob]:
    db_job = db.query(models.IngestionJob).filter(models.IngestionJob.id == job_id).first()
    if not db_job:
        return None
    db_job.status = "pending"
    db_job.last_error = None
    db.commit()
    db.refresh(db_job)
    return db_job

# --- Audit Log ---

def get_audit_logs(db: Session, skip: int = 0, limit: int = 100) -> List[models.AuditLog]:
    return db.query(models.AuditLog).order_by(desc(models.AuditLog.created_at)).offset(skip).limit(limit).all()

def create_audit_log(db: Session, api_key_id: Optional[UUID], route: str, scope: Optional[str], action: str) -> models.AuditLog:
    db_log = models.AuditLog(
        api_key_id=api_key_id,
        route=route,
        scope=scope,
        action=action
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

# --- Memory Stats ---

def get_memory_stats(db: Session) -> Dict[str, any]:
    total = db.query(models.Memory).count()
    by_status = dict(db.query(models.Memory.status, func.count(models.Memory.id)).group_by(models.Memory.status).all())
    by_scope = dict(db.query(models.Memory.scope, func.count(models.Memory.id)).group_by(models.Memory.scope).all())
    by_type = dict(db.query(models.Memory.type, func.count(models.Memory.id)).group_by(models.Memory.type).all())
    total_entities = db.query(models.Entity).count()
    pending_reviews = db.query(models.ReviewItem).filter(models.ReviewItem.status == "pending").count()
    pending_jobs = db.query(models.IngestionJob).filter(models.IngestionJob.status == "pending").count()
    return {
        "total": total,
        "by_status": by_status,
        "by_scope": by_scope,
        "by_type": by_type,
        "total_entities": total_entities,
        "pending_reviews": pending_reviews,
        "pending_jobs": pending_jobs,
    }

def bulk_reindex(db: Session, status_filter: Optional[str] = None, scope_filter: Optional[str] = None, force: bool = False) -> Dict[str, int]:
    query = db.query(models.Memory).filter(models.Memory.status != "archived")
    if status_filter:
        query = query.filter(models.Memory.status == status_filter)
    if scope_filter:
        query = query.filter(models.Memory.scope == scope_filter)

    memories = query.all()
    queued = 0
    skipped = 0

    for memory in memories:
        if not memory.content:
            skipped += 1
            continue

        if not force:
            has_chunks = db.query(models.MemoryChunk).filter(models.MemoryChunk.memory_id == memory.id).first()
            if has_chunks:
                continue

        db.query(models.MemoryChunk).filter(models.MemoryChunk.memory_id == memory.id).delete()
        db_job = models.IngestionJob(
            memory_id=memory.id,
            job_type="re_embed",
            status="pending",
            payload={"action": "chunk_and_embed"}
        )
        db.add(db_job)
        queued += 1

    db.commit()
    return {"queued": queued, "skipped_no_content": skipped}