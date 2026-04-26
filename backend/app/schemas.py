from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict

class EntityBase(BaseModel):
    type: str
    name: str
    description: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = None

class EntityCreate(EntityBase):
    pass

class EntityResponse(EntityBase):
    id: UUID
    normalized_name: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MemoryBase(BaseModel):
    type: str
    title: Optional[str] = None
    content: str
    scope: str
    sensitivity: str = "internal"
    confidence: Optional[float] = None
    source_id: Optional[UUID] = None
    entity_id: Optional[UUID] = None
    canonical_group_id: Optional[UUID] = None
    supersedes_memory_id: Optional[UUID] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    observed_at: Optional[datetime] = None
    metadata_: Optional[Dict[str, Any]] = None

class MemoryCreate(MemoryBase):
    pass

class MemoryResponse(MemoryBase):
    id: UUID
    status: str
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MemorySearchQuery(BaseModel):
    query: str
    scopes: Optional[List[str]] = None
    type: Optional[str] = None
    entity_id: Optional[UUID] = None
    include_scratch: bool = False
    include_invalidated: bool = False
    limit: int = 10
    threshold: float = 2.0

class ReviewItemResponse(BaseModel):
    id: UUID
    review_type: str
    status: str
    memory_id: UUID
    candidate_memory_id: Optional[UUID] = None
    reason: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    confidence: Optional[float] = None
    canonical_group_id: Optional[UUID] = None
    supersedes_memory_id: Optional[UUID] = None
    valid_until: Optional[datetime] = None
    invalidate_previous: bool = True

class ReviewItemResolve(BaseModel):
    action: str  # e.g., "merge", "supersede", "archive_candidate", "keep_both", "promote_canonical"
    resolution_notes: Optional[str] = None

# --- API Key Schemas ---

class APIKeyCreate(BaseModel):
    name: str
    allowed_scopes: List[str] = ["coding_projects"]
    can_read: bool = True
    can_write: bool = True

class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    allowed_scopes: List[str]
    can_read: bool
    can_write: bool
    active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class APIKeyCreateResponse(BaseModel):
    id: UUID
    name: str
    allowed_scopes: List[str]
    can_read: bool
    can_write: bool
    active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    plain_key: str

# --- Ingestion Job Schemas ---

class IngestionJobResponse(BaseModel):
    id: UUID
    memory_id: Optional[UUID] = None
    job_type: str
    status: str
    attempt_count: int = 0
    last_error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Audit Log Schemas ---

class AuditLogResponse(BaseModel):
    id: UUID
    api_key_id: Optional[UUID] = None
    route: str
    scope: Optional[str] = None
    action: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Memory Stats ---

class MemoryStatsResponse(BaseModel):
    total: int
    by_status: Dict[str, int]
    by_scope: Dict[str, int]
    by_type: Dict[str, int]
    total_entities: int
    pending_reviews: int
    pending_jobs: int

class BulkReindexResponse(BaseModel):
    queued: int
    skipped_no_content: int
    message: str

    class Config:
        from_attributes = True