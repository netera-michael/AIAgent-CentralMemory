import json
import sys
import argparse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Memory, IngestionJob
from app.crud import calculate_content_hash

def import_bulk(file_path: str, scope: str, type_override: str = None):
    """
    Imports a list of JSON objects into the database as `scratch`.
    Format expected: [{"content": "...", "type": "...", "title": "...", "summary": "..."}]
    """
    with open(file_path, "r") as f:
        data = json.load(f)
        
    db = SessionLocal()
    imported_count = 0
    skipped_count = 0
    
    try:
        for item in data:
            content = item.get("content")
            if not content:
                continue
                
            content_hash = calculate_content_hash(content)
            existing = db.query(Memory).filter(Memory.content_hash == content_hash).first()
            
            if existing:
                skipped_count += 1
                continue
                
            mem = Memory(
                type=type_override or item.get("type", "fact"),
                title=item.get("title"),
                content=content,
                content_hash=content_hash,
                summary=item.get("summary"),
                scope=scope,
                sensitivity="internal",
                status="scratch",
                confidence=0.3 # Low confidence for bulk imports
            )
            db.add(mem)
            db.flush()
            
            job = IngestionJob(
                memory_id=mem.id,
                job_type="ingest_memory",
                status="pending",
                payload={"action": "chunk_and_embed"}
            )
            db.add(job)
            
            imported_count += 1
            
        db.commit()
        print(f"Successfully imported {imported_count} records. Skipped {skipped_count} exact duplicates.")
        print("Pre-clustering (Review Queue deduplication) should be run as a separate admin task.")
    except Exception as e:
        db.rollback()
        print(f"Error during import: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk Import Script for CentralMemory")
    parser.add_argument("file", help="Path to JSON file containing array of memories")
    parser.add_argument("--scope", required=True, help="Scope to assign to all imported memories (e.g. personal)")
    parser.add_argument("--type", help="Override type for all imported memories")
    
    args = parser.parse_args()
    import_bulk(args.file, args.scope, args.type)