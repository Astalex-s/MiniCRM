"""API: сделки."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import CRMDatabase
from ..deps import get_db
from ..models import Deal, DealCreate, DealUpdate

router = APIRouter()


@router.post("", response_model=Deal)
def create(payload: DealCreate, db: CRMDatabase = Depends(get_db)):
    return db.deal_create(
        title=payload.title,
        client_id=payload.client_id,
        amount=payload.amount,
        status=payload.status,
        notes=payload.notes,
    )


@router.get("", response_model=List[Deal])
def list_(
    db: CRMDatabase = Depends(get_db),
    client_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return db.deal_list(client_id=client_id, status=status, limit=limit, offset=offset)


@router.get("/search", response_model=List[Deal])
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    db: CRMDatabase = Depends(get_db),
):
    return db.deal_search(q=q, limit=limit)


@router.get("/{deal_id}", response_model=Deal)
def get(deal_id: int, db: CRMDatabase = Depends(get_db)):
    row = db.deal_get(deal_id)
    if not row:
        raise HTTPException(status_code=404, detail="Deal not found")
    return row


@router.patch("/{deal_id}", response_model=Deal)
def update(deal_id: int, payload: DealUpdate, db: CRMDatabase = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    row = db.deal_update(deal_id, **data)
    if not row:
        raise HTTPException(status_code=404, detail="Deal not found")
    return row


@router.delete("/{deal_id}")
def delete(deal_id: int, db: CRMDatabase = Depends(get_db)):
    if not db.deal_delete(deal_id):
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"ok": True}
