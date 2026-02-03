"""API: задачи."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import CRMDatabase
from ..deps import get_db
from ..models import Task, TaskCreate, TaskUpdate

router = APIRouter()


@router.post("", response_model=Task)
def create(payload: TaskCreate, db: CRMDatabase = Depends(get_db)):
    return db.task_create(
        title=payload.title,
        description=payload.description,
        client_id=payload.client_id,
        deal_id=payload.deal_id,
        is_completed=payload.is_completed,
        due_date=payload.due_date,
    )


@router.get("", response_model=List[Task])
def list_(
    db: CRMDatabase = Depends(get_db),
    client_id: Optional[int] = Query(None),
    deal_id: Optional[int] = Query(None),
    is_completed: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return db.task_list(
        client_id=client_id,
        deal_id=deal_id,
        is_completed=is_completed,
        limit=limit,
        offset=offset,
    )


@router.get("/{task_id}", response_model=Task)
def get(task_id: int, db: CRMDatabase = Depends(get_db)):
    row = db.task_get(task_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@router.patch("/{task_id}", response_model=Task)
def update(task_id: int, payload: TaskUpdate, db: CRMDatabase = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    row = db.task_update(task_id, **data)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@router.delete("/{task_id}")
def delete(task_id: int, db: CRMDatabase = Depends(get_db)):
    if not db.task_delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@router.post("/{task_id}/complete", response_model=Task)
def complete(
    task_id: int,
    completed: bool = Query(True),
    db: CRMDatabase = Depends(get_db),
):
    row = db.task_set_completed(task_id, completed)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return row
