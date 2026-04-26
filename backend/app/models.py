import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Numeric, Boolean, Integer, ForeignKey, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from .database import Base

_status_lifecycle = "scratch, reviewed, canonical, stale, conflicted, archived"
_review_types = "duplicate_cluster, conflict_candidate, stale_candidate"

class Memory(Base):
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    content_hash = Column(Text, unique=True, nullable=False)
    summary = Column(Text, nullable=True)
    scope = Column(Text, nullable=False)
    sensitivity = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="scratch")
    confidence = Column(Numeric, nullable=True)
    
    source_id = Column(UUID(as_uuid=True), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    canonical_group_id = Column(UUID(as_uuid=True), nullable=True)
    supersedes_memory_id = Column(UUID(as_uuid=True), nullable=True)
    
    valid_from = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    observed_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    
    _metadata = Column("metadata", JSONB, nullable=True)

    @property
    def metadata_(self):
        return self._metadata

    @metadata_.setter
    def metadata_(self, value):
        self._metadata = value

class MemoryChunk(Base):
    __tablename__ = "memory_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))  # nomic-embed-text is 768 dims
    embedding_model = Column(Text, nullable=False)
    embedding_model_version = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Entity(Base):
    __tablename__ = "entities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    normalized_name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    _metadata = Column("metadata", JSONB, nullable=True)

    @property
    def metadata_(self):
        return self._metadata

    @metadata_.setter
    def metadata_(self, value):
        self._metadata = value

class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    external_ref = Column(Text, nullable=True)
    trust_score = Column(Numeric, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    _metadata = Column("metadata", JSONB, nullable=True)

    @property
    def metadata_(self):
        return self._metadata

    @metadata_.setter
    def metadata_(self, value):
        self._metadata = value

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, unique=True, nullable=False)
    hashed_key = Column(Text, nullable=False)
    allowed_scopes = Column(ARRAY(Text), nullable=False)
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    _metadata = Column("metadata", JSONB, nullable=True)

    @property
    def metadata_(self):
        return self._metadata

    @metadata_.setter
    def metadata_(self, value):
        self._metadata = value

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="SET NULL"), nullable=True)
    job_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="pending")
    attempt_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    payload = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ReviewItem(Base):
    __tablename__ = "review_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="pending")
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    candidate_memory_id = Column(UUID(as_uuid=True), nullable=True)
    reason = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True)
    route = Column(Text, nullable=False)
    scope = Column(Text, nullable=True)
    action = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))