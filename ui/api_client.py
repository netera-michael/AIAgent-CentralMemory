import os
import requests
from typing import Dict, Any, List, Optional

API_KEY = os.getenv("ADMIN_API_KEY") or os.getenv("CENTRALMEMORY_API_KEY", "")

if not API_KEY:
    import sys
    print("WARNING: No ADMIN_API_KEY or CENTRALMEMORY_API_KEY set. UI will fail to authenticate.", file=sys.stderr)

class CentralMemoryAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }

    def get_health(self) -> Dict[str, Any]:
        res = requests.get(f"{self.base_url}/health", headers=self.headers)
        res.raise_for_status()
        return res.json()

    # --- Memories ---

    def get_memories(self, skip: int = 0, limit: int = 50, include_scratch: bool = False) -> List[Dict[str, Any]]:
        res = requests.get(
            f"{self.base_url}/memories",
            params={"skip": skip, "limit": limit, "include_scratch": include_scratch},
            headers=self.headers
        )
        res.raise_for_status()
        return res.json()

    def get_memory(self, memory_id: str) -> Dict[str, Any]:
        res = requests.get(f"{self.base_url}/memories/{memory_id}", headers=self.headers)
        res.raise_for_status()
        return res.json()

    def create_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/memories", json=data, headers=self.headers)
        res.raise_for_status()
        return res.json()

    def update_memory(self, memory_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        res = requests.patch(f"{self.base_url}/memories/{memory_id}", json=data, headers=self.headers)
        res.raise_for_status()
        return res.json()

    def archive_memory(self, memory_id: str) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/memories/{memory_id}/archive", headers=self.headers)
        res.raise_for_status()
        return res.json()

    def purge_memory(self, memory_id: str) -> None:
        res = requests.delete(f"{self.base_url}/memories/{memory_id}/purge", headers=self.headers)
        res.raise_for_status()

    # --- Entities ---

    def get_entities(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        res = requests.get(
            f"{self.base_url}/entities",
            params={"skip": skip, "limit": limit},
            headers=self.headers
        )
        res.raise_for_status()
        return res.json()

    def create_entity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/entities", json=data, headers=self.headers)
        res.raise_for_status()
        return res.json()

    # --- Search ---

    def semantic_search(self, query: str, scopes: Optional[List[str]] = None,
                        type: Optional[str] = None, entity_id: Optional[str] = None,
                        include_scratch: bool = False, limit: int = 10,
                        threshold: float = 0.5) -> List[Dict[str, Any]]:
        payload = {
            "query": query,
            "include_scratch": include_scratch,
            "limit": limit,
            "threshold": threshold
        }
        if scopes:
            payload["scopes"] = scopes
        if type:
            payload["type"] = type
        if entity_id:
            payload["entity_id"] = entity_id
        res = requests.post(f"{self.base_url}/search/semantic", json=payload, headers=self.headers)
        res.raise_for_status()
        return res.json()

    # --- Review Items ---

    def get_review_items(self, status: str = "pending") -> List[Dict[str, Any]]:
        res = requests.get(f"{self.base_url}/review-items", params={"status": status}, headers=self.headers)
        res.raise_for_status()
        return res.json()

    def resolve_review_item(self, item_id: str, action: str, notes: str = "") -> Dict[str, Any]:
        payload = {"action": action, "resolution_notes": notes}
        res = requests.post(f"{self.base_url}/review-items/{item_id}/resolve", json=payload, headers=self.headers)
        res.raise_for_status()
        return res.json()

    # --- Stats ---

    def get_stats(self) -> Dict[str, Any]:
        res = requests.get(f"{self.base_url}/stats", headers=self.headers)
        res.raise_for_status()
        return res.json()

    # --- Ingestion Jobs ---

    def get_ingestion_jobs(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        res = requests.get(f"{self.base_url}/ingestion-jobs", params=params, headers=self.headers)
        res.raise_for_status()
        return res.json()

    def retry_ingestion_job(self, job_id: str) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/ingestion-jobs/{job_id}/retry", headers=self.headers)
        res.raise_for_status()
        return res.json()

    # --- API Keys ---

    def get_api_keys(self) -> List[Dict[str, Any]]:
        res = requests.get(f"{self.base_url}/api-keys", headers=self.headers)
        res.raise_for_status()
        return res.json()

    def create_api_key(self, data: Dict[str, Any]) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/api-keys", json=data, headers=self.headers)
        res.raise_for_status()
        return res.json()

    def revoke_api_key(self, key_id: str) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/api-keys/{key_id}/revoke", headers=self.headers)
        res.raise_for_status()
        return res.json()

    # --- Audit Logs ---

    def get_audit_logs(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        res = requests.get(f"{self.base_url}/audit-logs", params={"skip": skip, "limit": limit}, headers=self.headers)
        res.raise_for_status()
        return res.json()
