# CentralMemory

A centralized memory platform for AI agents. Store facts, preferences, decisions, and project notes with semantic search, typed memories, a review workflow, and MCP integration. Built on PostgreSQL + pgvector.

## Why CentralMemory?

Most AI "memory" solutions are either:
- **Per-chat memory** — isolated to one conversation, lost when you switch clients
- **Cloud SaaS** — your data on someone else's server, with someone else's embeddings
- **RAG wrappers** — document retrieval masquerading as personal memory

CentralMemory is different:
- **Cross-client** — one memory store used by any AI agent, CLI tool, or chat UI
- **Self-hosted** — your data, your embeddings, your server
- **Human-governed** — typed memories with a status lifecycle (scratch → reviewed → canonical) and a review queue, not just a vector dump
- **Multi-signal retrieval** — composite scoring: vector similarity + BM25 keyword match + canonical boost + recency, not just cosine distance
- **Temporal invalidation** — memories can be superseded with `valid_from`/`valid_until`; old versions auto-archived
- **MCP-native** — streamable HTTP transport, works with any MCP-compatible client

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│  AI Client   │───▶│  CM API     │───▶│  PostgreSQL  │
│  (MCP/REST)  │    │  :8001      │    │  + pgvector  │
└─────────────┘    ├─────────────┤    └──────────────┘
                   │  MCP Server │         ▲
                   │  :9000      │         │
                   ├─────────────┤    ┌────┴─────┐
                   │  Worker     │───▶│  Ollama   │
                   │  (embed)    │    │  :11434   │
                   └─────────────┘    └──────────┘
```

- **API** — FastAPI REST API on port 8001
- **MCP** — Streamable HTTP server on port 9000 (10 tools: CRUD, search, entities, review, purge)
- **Worker** — Background process for chunking + embedding via Ollama
- **UI** — React + Chakra UI control panel on port 8501
- **Postgres** — pgvector/pgvector:pg16 with HNSW index for fast vector search

All services run in Docker Compose.

## Quick Start

### Prerequisites

- Docker + Docker Compose
- [Ollama](https://ollama.ai) running with the `nomic-embed-text` model

```bash
ollama pull nomic-embed-text
```

### 1. Clone and Configure

```bash
git clone https://github.com/netera-michael/AIAgent-CentralMemory.git
cd CentralMemory
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, ADMIN_API_KEY, and BIND_IP
```

### 2. Start Services

```bash
docker compose up -d
```

First startup will:
- Create the PostgreSQL database with pgvector extension
- Run `backend/init_db.sql` to create all tables and indexes
- Build and start API, Worker, MCP, and UI containers

### 3. Create an API Key

```bash
curl -X POST http://localhost:8001/api-keys \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_ADMIN_KEY_FROM_ENV" \
  -d '{"name": "my-agent", "allowed_scopes": ["personal"], "can_read": true, "can_write": true}'
```

Save the returned `plain_key` — it won't be shown again.

### 4. Test

```bash
# Health check
curl http://localhost:8001/health

# Add a memory
curl -X POST http://localhost:8001/memories \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"type": "fact", "scope": "personal", "content": "I prefer dark mode in all editors", "title": "Editor preference"}'

# Semantic search
curl -X POST http://localhost:8001/search/semantic \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"query": "editor settings", "limit": 5}'
```

## API Endpoints

All endpoints require `X-API-Key` header.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/memories` | Create a memory |
| GET | `/memories` | List memories |
| GET | `/memories/{id}` | Get memory by ID |
| PATCH | `/memories/{id}` | Update memory |
| POST | `/memories/{id}/archive` | Soft-delete |
| DELETE | `/memories/{id}/purge` | Hard delete (admin) |
| POST | `/search/semantic` | Multi-signal semantic search |
| POST | `/reindex` | Bulk reindex (admin) |
| POST | `/entities` | Create entity |
| GET | `/entities` | List entities |
| GET | `/review-items` | List review items (admin) |
| POST | `/review-items/{id}/resolve` | Resolve review item |
| GET | `/stats` | Memory statistics (admin) |
| GET | `/ingestion-jobs` | List jobs (admin) |
| POST | `/ingestion-jobs/{id}/retry` | Retry failed job |
| POST | `/api-keys` | Create API key (admin) |
| GET | `/api-keys` | List API keys (admin) |
| POST | `/api-keys/{id}/revoke` | Revoke key (admin) |
| GET | `/audit-logs` | View audit log (admin) |

## MCP Integration

CentralMemory exposes an MCP (Model Context Protocol) server via Streamable HTTP on port 9000. 10 tools available:

| Tool | Description |
|------|-------------|
| `memory_add` | Store a new memory |
| `memory_search` | Semantic search |
| `memory_get` | Get memory by ID |
| `memory_list` | List recent memories |
| `memory_update` | Update existing memory |
| `memory_archive` | Soft-delete a memory |
| `memory_purge` | Hard delete (admin) |
| `entity_get_or_create` | Ensure an entity exists |
| `review_list_conflicts` | List pending review items |
| `review_resolve` | Resolve a review item |

### LiteLLM / OpenCode / Claude Desktop

Add to your MCP client config:

```json
{
  "mcpServers": {
    "centralmemory": {
      "url": "http://localhost:9000/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

### LobeChat / Custom Router

For chat UIs, you can build a memory-router (FastAPI proxy) that:
1. Intercepts LLM requests
2. Recalls relevant memories via CM search
3. Injects them into the system prompt
4. Auto-extracts new facts from the response
5. Stores them back to CentralMemory

See [`AGENTS.md`](AGENTS.md) for memory quality guidelines.

## Data Model

### Memory Types & Scopes

Each memory has a **type** and **scope** for structured organization:

**Types**: `fact`, `preference`, `decision`, `workflow`, `project_note`, `conversation_episode`

**Scopes**: `personal`, `personal_finance`, `biz_finance`, `biz_projects`, `coding_projects`, `infrastructure`, `social_media_clients`

### Status Lifecycle

```
scratch → reviewed → canonical
                  ↘ stale
                  ↘ conflicted
                  ↘ archived
```

- **scratch** — just created, not yet verified
- **reviewed** — human or trusted agent confirmed
- **canonical** — critical truth, highest search boost
- **stale** / **conflicted** — flagged for review
- **archived** — soft-deleted, excluded from search

### Temporal Invalidation

Memories support `valid_from` / `valid_until`. When content is updated:
- Old version auto-archived as shadow copy with `valid_until=now()`
- New version gets `valid_from=now()`, `valid_until=NULL`
- `supersedes_memory_id` links them

### Multi-Signal Retrieval

Search scoring combines four signals:

| Signal | Weight | Description |
|--------|--------|-------------|
| Vector similarity | 60% | pgvector HNSW cosine distance on 768-dim embeddings |
| BM25 keyword match | 15% | PostgreSQL `tsvector` full-text search with GIN index |
| Canonical boost | 10% | `canonical` status gets +0.1, `reviewed` gets 0.0 |
| Recency | 5% | Newer memories get up to +0.05 |

### Chunking & Embedding

Long content is sentence-aware chunked (800 char target, 100 char overlap) and embedded as 768-dim vectors using `nomic-embed-text` via Ollama. HNSW index enables fast approximate nearest neighbor search.

## Configuration

See [`.env.example`](.env.example) for all environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `centralmemory` | DB user |
| `POSTGRES_PASSWORD` | `changeme_...` | DB password (change!) |
| `POSTGRES_DB` | `centralmemory` | DB name |
| `BIND_IP` | `127.0.0.1` | Bind address (use Tailscale IP for remote) |
| `ADMIN_API_KEY` | — | Required for admin endpoints |
| `CENTRALMEMORY_API_KEY` | — | Required for MCP server |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Ollama embedding model |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama URL from Docker |

## Reindexing

After changing the embedding model or chunking parameters:

```bash
# Full reindex
curl -X POST "http://localhost:8001/reindex?force=true" \
  -H "X-API-Key: YOUR_ADMIN_KEY"

# Scoped reindex
curl -X POST "http://localhost:8001/reindex?force=true&scope=personal" \
  -H "X-API-Key: YOUR_ADMIN_KEY"
```

## Comparison

| Feature | CentralMemory | Zep | Mem0 |
|---------|--------------|-----|------|
| Self-hosted | ✅ | ✅ (SSPL) | ❌ (cloud or Enterprise) |
| Typed memories | ✅ | ❌ | ❌ |
| Status lifecycle | ✅ scratch/reviewed/canonical | ❌ | ❌ |
| Review queue | ✅ | ❌ | ❌ |
| Temporal invalidation | ✅ valid_from/valid_until | ✅ | ❌ |
| Multi-signal retrieval | ✅ vector+BM25+boosts | ✅ | vector only |
| MCP server | ✅ Streamable HTTP | ❌ | ❌ |
| Entity grouping | ✅ | ✅ | ✅ |
| Open source | ✅ Apache 2.0 | ⚠️ SSPL | ❌ |
| Embedding model | Any Ollama model | OpenAI/local | OpenAI |

## License

Apache License 2.0 — see [LICENSE](LICENSE).