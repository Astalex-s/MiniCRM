"""
Модели данных для мини-CRM.
Таблицы и типы совместимы с SQLite 3.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# --- SQLite: типы INTEGER, TEXT, REAL, BLOB. Нет BOOLEAN — используем INTEGER 0/1. ---

# Статусы клиента
CLIENT_STATUS_ACTIVE = "active"
CLIENT_STATUS_ARCHIVED = "archived"

# Статусы сделки
DEAL_STATUS_DRAFT = "draft"
DEAL_STATUS_IN_PROGRESS = "in_progress"
DEAL_STATUS_WON = "won"
DEAL_STATUS_LOST = "lost"


# ============== Pydantic-модели для API ==============

class ClientBase(BaseModel):
    name: str = Field(..., min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = Field(default=CLIENT_STATUS_ACTIVE)
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class Client(ClientBase):
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# --- Сделки ---

class DealBase(BaseModel):
    title: str = Field(..., min_length=1)
    client_id: Optional[int] = None
    amount: Optional[float] = None
    status: str = Field(default=DEAL_STATUS_DRAFT)
    notes: Optional[str] = None


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    client_id: Optional[int] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class Deal(DealBase):
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# --- Задачи / напоминания ---

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    client_id: Optional[int] = None
    deal_id: Optional[int] = None
    is_completed: bool = False
    due_date: Optional[str] = None  # ISO date/datetime string


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    client_id: Optional[int] = None
    deal_id: Optional[int] = None
    is_completed: Optional[bool] = None
    due_date: Optional[str] = None


class Task(TaskBase):
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ============== Схемы таблиц SQLite ==============
# Используются при создании таблиц в database.py

TABLE_CLIENTS = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

TABLE_DEALS = """
CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    title TEXT NOT NULL,
    amount REAL,
    status TEXT NOT NULL DEFAULT 'draft',
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);
"""

TABLE_TASKS = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    client_id INTEGER,
    deal_id INTEGER,
    is_completed INTEGER NOT NULL DEFAULT 0,
    due_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (deal_id) REFERENCES deals(id)
);
"""

ALL_TABLES = [TABLE_CLIENTS, TABLE_DEALS, TABLE_TASKS]
