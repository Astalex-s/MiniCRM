"""
FastAPI-бэкенд мини-CRM.
Эндпоинты для клиентов, сделок и задач.
"""
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from .database import CRMDatabase
from .models import (
    Client,
    ClientCreate,
    ClientUpdate,
    Deal,
    DealCreate,
    DealUpdate,
    Task,
    TaskCreate,
    TaskUpdate,
)

# Файл БД рядом с пакетом crm
DB_PATH = Path(__file__).resolve().parent.parent / "crm.db"

# Корень проекта в path для импорта log
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from log import setup_logging, get_logger

setup_logging(log_file="crm.log", console=True)
logger = get_logger("crm.api")

app = FastAPI(title="Mini CRM API", version="0.1.0")
db = CRMDatabase(str(DB_PATH))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование входящих запросов и ответов."""
    method = request.method
    path = request.url.path
    logger.info("Request: %s %s", method, path)
    try:
        response = await call_next(request)
        logger.info("Response: %s %s -> %s", method, path, response.status_code)
        return response
    except Exception as e:
        logger.exception("Error handling %s %s: %s", method, path, e)
        raise


# ---------- Клиенты ----------

@app.post("/clients", response_model=Client)
def client_create(payload: ClientCreate):
    """Создать клиента."""
    return db.client_create(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        status=payload.status,
        notes=payload.notes,
    )


@app.get("/clients", response_model=List[Client])
def client_list(
    status: Optional[str] = Query(None, description="active | archived"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Список клиентов с фильтром по статусу."""
    return db.client_list(status=status, limit=limit, offset=offset)


@app.get("/clients/search", response_model=List[Client])
def client_search(q: str = Query(..., min_length=1), limit: int = Query(50, ge=1, le=200)):
    """Поиск клиентов по имени, email, телефону, заметкам (LIKE)."""
    return db.client_search(q=q, limit=limit)


@app.get("/clients/{client_id}", response_model=Client)
def client_get(client_id: int):
    """Получить клиента по id."""
    row = db.client_get(client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return row


@app.patch("/clients/{client_id}", response_model=Client)
def client_update(client_id: int, payload: ClientUpdate):
    """Обновить клиента."""
    data = payload.model_dump(exclude_unset=True)
    row = db.client_update(client_id, **data)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return row


@app.delete("/clients/{client_id}")
def client_delete(client_id: int):
    """Удалить клиента навсегда."""
    if not db.client_delete(client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    return {"ok": True}


@app.post("/clients/{client_id}/archive", response_model=Client)
def client_archive(client_id: int):
    """Архивировать клиента."""
    row = db.client_archive(client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return row


# ---------- Сделки ----------

@app.post("/deals", response_model=Deal)
def deal_create(payload: DealCreate):
    """Создать сделку (клиент опционален)."""
    return db.deal_create(
        title=payload.title,
        client_id=payload.client_id,
        amount=payload.amount,
        status=payload.status,
        notes=payload.notes,
    )


@app.get("/deals", response_model=List[Deal])
def deal_list(
    client_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Список сделок с фильтрами."""
    return db.deal_list(client_id=client_id, status=status, limit=limit, offset=offset)


@app.get("/deals/search", response_model=List[Deal])
def deal_search(q: str = Query(..., min_length=1), limit: int = Query(50, ge=1, le=200)):
    """Поиск сделок по названию и заметкам (LIKE)."""
    return db.deal_search(q=q, limit=limit)


@app.get("/deals/{deal_id}", response_model=Deal)
def deal_get(deal_id: int):
    """Получить сделку по id."""
    row = db.deal_get(deal_id)
    if not row:
        raise HTTPException(status_code=404, detail="Deal not found")
    return row


@app.patch("/deals/{deal_id}", response_model=Deal)
def deal_update(deal_id: int, payload: DealUpdate):
    """Обновить сделку (в т.ч. привязать/отвязать клиента, статус)."""
    data = payload.model_dump(exclude_unset=True)
    row = db.deal_update(deal_id, **data)
    if not row:
        raise HTTPException(status_code=404, detail="Deal not found")
    return row


@app.delete("/deals/{deal_id}")
def deal_delete(deal_id: int):
    """Удалить сделку."""
    if not db.deal_delete(deal_id):
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"ok": True}


# ---------- Задачи ----------

@app.post("/tasks", response_model=Task)
def task_create(payload: TaskCreate):
    """Создать задачу/напоминание (привязка к клиенту/сделке опциональна)."""
    return db.task_create(
        title=payload.title,
        description=payload.description,
        client_id=payload.client_id,
        deal_id=payload.deal_id,
        is_completed=payload.is_completed,
        due_date=payload.due_date,
    )


@app.get("/tasks", response_model=List[Task])
def task_list(
    client_id: Optional[int] = Query(None),
    deal_id: Optional[int] = Query(None),
    is_completed: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Список задач с фильтрами."""
    return db.task_list(
        client_id=client_id,
        deal_id=deal_id,
        is_completed=is_completed,
        limit=limit,
        offset=offset,
    )


@app.get("/tasks/{task_id}", response_model=Task)
def task_get(task_id: int):
    """Получить задачу по id."""
    row = db.task_get(task_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@app.patch("/tasks/{task_id}", response_model=Task)
def task_update(task_id: int, payload: TaskUpdate):
    """Обновить задачу (в т.ч. отметить выполненной/невыполненной)."""
    data = payload.model_dump(exclude_unset=True)
    row = db.task_update(task_id, **data)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@app.delete("/tasks/{task_id}")
def task_delete(task_id: int):
    """Удалить задачу."""
    if not db.task_delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@app.post("/tasks/{task_id}/complete", response_model=Task)
def task_complete(task_id: int, completed: bool = Query(True)):
    """Отметить задачу выполненной или невыполненной."""
    row = db.task_set_completed(task_id, completed)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@app.get("/")
def root():
    """Корневой путь: информация об API и ссылки."""
    return {
        "app": "Mini CRM API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    """Проверка работы API."""
    return {"status": "ok"}


@app.on_event("startup")
def startup():
    logger.info("CRM API started, DB: %s", DB_PATH)
