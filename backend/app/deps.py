from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from hashlib import sha256

from . import models
from .database import get_db

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER_SECURITY = HTTPBearer(auto_error=False)


def _extract_api_key(
    api_key: Optional[str] = Depends(API_KEY_HEADER),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(BEARER_SECURITY),
) -> Optional[str]:
    if api_key:
        return api_key
    if bearer:
        return bearer.credentials
    return None


def _hash_key(key: str) -> str:
    return sha256(key.encode()).hexdigest()


def _lookup_key(db: Session, raw_key: str) -> Optional[models.APIKey]:
    hashed = _hash_key(raw_key)
    return db.query(models.APIKey).filter(
        models.APIKey.hashed_key == hashed,
        models.APIKey.active == True,
    ).first()


def get_current_scopes(
    request: Request,
    db: Session = Depends(get_db),
    raw_key: str = Depends(_extract_api_key),
) -> List[str]:
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    record = _lookup_key(db, raw_key)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    record.last_used_at = datetime.now(timezone.utc)
    db.commit()

    return record.allowed_scopes


def get_api_key_record(
    request: Request,
    db: Session = Depends(get_db),
    raw_key: str = Depends(_extract_api_key),
) -> Optional[models.APIKey]:
    if not raw_key:
        return None
    return _lookup_key(db, raw_key)