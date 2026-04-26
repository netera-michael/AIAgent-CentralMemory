import argparse
import yaml
import sys
from app.database import SessionLocal
from app.models import Memory, MemoryChunk
from app.worker import generate_embedding

def load_cases(file_path: str):
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)
    return data.get("cases", [])

def run_eval(cases):
    db = SessionLocal()
    success_count = 0
    total = len(cases)
    
    print(f"Running {total} retrieval evaluation cases...")
    print("-" * 50)
    
    try:
        for idx, case in enumerate(cases):
            query_str = case["query"]
            expected_match = case.get("expected_content_match", "").lower()
            
            try:
                query_embedding = generate_embedding(query_str)
            except Exception as e:
                print(f"[{idx+1}/{total}] FAIL: Embedding generation failed - {e}")
                continue
                
            # Perform search
            results = db.query(Memory).join(MemoryChunk).order_by(
                MemoryChunk.embedding.cosine_distance(query_embedding)
            ).filter(
                Memory.status.in_(["reviewed", "canonical"])
            ).distinct().limit(5).all()
            
            # Check if expected match is in top 5
            found = False
            for rank, r in enumerate(results):
                if expected_match in r.content.lower():
                    found = True
                    break
                    
            if found:
                print(f"[{idx+1}/{total}] PASS: '{query_str}' -> found '{expected_match}' at rank {rank+1}")
                success_count += 1
            else:
                print(f"[{idx+1}/{total}] FAIL: '{query_str}' -> missed '{expected_match}'")
                print(f"   Notes: {case.get('notes', '')}")
                if results:
                    print("   Top result was:")
                    print(f"   {results[0].content[:100]}...")
                
    finally:
        db.close()
        
    print("-" * 50)
    print(f"Score: {success_count}/{total} ({(success_count/total)*100:.1f}%)")
    
    if success_count < total:
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CentralMemory CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    eval_parser = subparsers.add_parser("eval", help="Run retrieval evaluation")
    eval_parser.add_argument("--file", default="retrieval_eval.yaml", help="Path to cases YAML")
    
    args = parser.parse_args()
    
    if args.command == "eval":
        cases = load_cases(args.file)
        if not cases:
            print("No cases found.")
            sys.exit(0)
        run_eval(cases)
    else:
        parser.print_help()