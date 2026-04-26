-- CentralMemory Database Schema
-- Run this file as the init script for a fresh PostgreSQL + pgvector database.
-- Docker Compose auto-executes files in /docker-entrypoint-initdb.d/ on first startup.

-- 1. Enable pgvector extension (required before any vector columns)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Memories table — canonical record store
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    content_hash TEXT UNIQUE NOT NULL,
    scope TEXT NOT NULL,
    sensitivity TEXT NOT NULL DEFAULT 'internal',
    status TEXT NOT NULL DEFAULT 'scratch',
    confidence NUMERIC,
    source_id UUID,
    entity_id UUID,
    canonical_group_id UUID,
    supersedes_memory_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    observed_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

-- 3. Memory chunks — vector-indexed text segments for semantic search
CREATE TABLE IF NOT EXISTS memory_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    embedding_model TEXT NOT NULL,
    embedding_model_version TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HNSW index for fast approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS ix_memory_chunks_embedding_hnsw
    ON memory_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Index on memory_id for chunk lookups
CREATE INDEX IF NOT EXISTS ix_memory_chunks_memory_id ON memory_chunks(memory_id);

-- 4. Entities — normalized subjects (person, project, server, etc.)
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_entities_normalized_name ON entities(normalized_name);

-- 5. Sources — provenance tracking
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    external_ref TEXT,
    trust_score NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- 6. API Keys — per-client authentication
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    hashed_key TEXT NOT NULL,
    allowed_scopes TEXT[] NOT NULL,
    can_read BOOLEAN DEFAULT TRUE,
    can_write BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- 7. Ingestion Jobs — async work tracking (chunking + embedding)
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID REFERENCES memories(id) ON DELETE SET NULL,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempt_count INTEGER DEFAULT 0,
    last_error TEXT,
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ingestion_jobs_status ON ingestion_jobs(status);

-- 8. Review Items — duplicate/conflict/staleness queue
CREATE TABLE IF NOT EXISTS review_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    candidate_memory_id UUID,
    reason TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_review_items_status ON review_items(status);

-- 9. Audit Log — append-only
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    route TEXT NOT NULL,
    scope TEXT,
    action TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. Helpful indexes for common queries
CREATE INDEX IF NOT EXISTS ix_memories_status ON memories(status);
CREATE INDEX IF NOT EXISTS ix_memories_scope ON memories(scope);
CREATE INDEX IF NOT EXISTS ix_memories_content_hash ON memories(content_hash);
CREATE INDEX IF NOT EXISTS ix_memories_created_at ON memories(created_at DESC);