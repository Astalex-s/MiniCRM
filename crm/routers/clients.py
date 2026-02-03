"""API: клиенты."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import CRMDatabase
from ..deps import get_db
from ..models import Client, ClientCreate, ClientUpdate

router = APIRouter()


@router.post("", response_model=Client)
def create(payload: ClientCreate, db: CRMDatabase = Depends(get_db)):
    return db.client_create(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        status=payload.status,
        notes=payload.notes,
    )


@router.get("", response_model=List[Client])
def list_(
    db: CRMDatabase = Depends(get_db),
    status: Optional[str] = Query(None, description="active | archived"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return db.client_list(status=status, limit=limit, offset=offset)


@router.get("/search", response_model=List[Client])
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    db: CRMDatabase = Depends(get_db),
):
    return db.client_search(q=q, limit=limit)


@router.get("/{client_id}", response_model=Client)
def get(client_id: int, db: CRMDatabase = Depends(get_db)):
    row = db.client_get(client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return row


@router.patch("/{client_id}", response_model=Client)
def update(client_id: int, payload: ClientUpdate, db: CRMDatabase = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    row = db.client_update(client_id, **data)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return row


@router.delete("/{client_id}")
def delete(client_id: int, db: CRMDatabase = Depends(get_db)):
    if not db.client_delete(client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    return {"ok": True}


@router.post("/{client_id}/archive", response_model=Client)
def archive(client_id: int, db: CRMDatabase = Depends(get_db)):
    row = db.client_archive(client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return row
