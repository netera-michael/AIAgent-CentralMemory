from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, text, case, and_
from pgvector.sqlalchemy import Vector
from typing import List, Optional
from . import schemas, crud, models
from .database import get_db
from .deps import get_current_scopes
from .worker import generate_embedding
import re

router = APIRouter(prefix="/search", tags=["search"])

def tokenize_for_tsquery(query: str) -> str:
    cleaned = re.sub(r'[^\w\s]', ' ', query.lower())
    tokens = cleaned.split()
    return " & ".join(t for t in tokens if len(t) > 1) or ""

@router.post("/semantic", response_model=List[schemas.MemoryResponse])
def semantic_search(
    query: schemas.MemorySearchQuery, 
    db: Session = Depends(get_db),
    scopes: List[str] = Depends(get_current_scopes)
):
    allowed_scopes = set(scopes)
    if "admin" in allowed_scopes:
        search_scopes = query.scopes if query.scopes else []
    else:
        if query.scopes:
             search_scopes = [s for s in query.scopes if s in allowed_scopes]
             if not search_scopes:
                 raise HTTPException(status_code=403, detail="No authorized scopes provided in query.")
        else:
            search_scopes = list(allowed_scopes)

    try:
        query_embedding = generate_embedding(query.query)
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to generate embedding for query: {e}")

    distance_expr = models.MemoryChunk.embedding.cosine_distance(query_embedding)
    subq = (
        db.query(
            models.MemoryChunk.memory_id,
            func.min(distance_expr).label("min_distance")
        )
        .group_by(models.MemoryChunk.memory_id)
        .subquery()
    )

    db_query = (
        db.query(models.Memory, subq.c.min_distance.label("vector_distance"))
        .join(subq, models.Memory.id == subq.c.memory_id)
    )

    if search_scopes and "admin" not in allowed_scopes:
         db_query = db_query.filter(models.Memory.scope.in_(search_scopes))
         
    if query.type:
        db_query = db_query.filter(models.Memory.type == query.type)

    if query.entity_id:
         db_query = db_query.filter(models.Memory.entity_id == query.entity_id)

    if not query.include_scratch:
        db_query = db_query.filter(models.Memory.status.in_(["reviewed", "canonical"]))

    if not query.include_invalidated:
        db_query = db_query.filter(
            and_(
                models.Memory.valid_until.is_(None),
                models.Memory.status != "archived"
            )
        )

    db_query = db_query.filter(subq.c.min_distance <= query.threshold)

    # Multi-signal scoring:
    # 1. Vector distance (lower = better, inverted to score)
    # 2. BM25 keyword match via tsvector (PostgreSQL full-text)
    # 3. Status boost: canonical > reviewed
    # 4. Recency boost: newer memories get slight boost
    
    ts_query_str = tokenize_for_tsquery(query.query)
    
    bm25_expr = func.to_tsvector(
        "english",
        func.coalesce(models.Memory.title, "") + text("' '") + func.coalesce(models.Memory.content, "")
    ).op("@@")(func.to_tsquery("english", text(f"'{ts_query_str}'")))
    
    bm25_score = case((bm25_expr, 0.15), else_=0.0)
    
    status_score = case(
        (models.Memory.status == "canonical", 0.1),
        (models.Memory.status == "reviewed", 0.0),
        else_=0.0
    )
    
    recency_score = text("""
        CASE WHEN memories.created_at IS NOT NULL 
        THEN LEAST(0.05, EXTRACT(EPOCH FROM (NOW() - memories.created_at)) / -157680000.0 + 0.05)
        ELSE 0 END
    """)

    composite_score = (
        (1.0 - subq.c.min_distance) * 0.6
        + bm25_score
        + status_score
        + recency_score
    )

    db_query = db_query.add_columns(composite_score.label("relevance_score"))
    db_query = db_query.order_by(desc("relevance_score"))

    rows = db_query.limit(query.limit).all()
    
    return [row[0] for row in rows]