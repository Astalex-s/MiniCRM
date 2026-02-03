"""
Слой работы с SQLite 3 для мини-CRM.
Класс CRUD создаёт таблицы при инициализации, если их нет.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import ALL_TABLES


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_client(row: tuple) -> dict:
    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "phone": row[3],
        "status": row[4],
        "notes": row[5],
        "created_at": row[6],
        "updated_at": row[7],
    }


def _row_to_deal(row: tuple) -> dict:
    return {
        "id": row[0],
        "client_id": row[1],
        "title": row[2],
        "amount": row[3],
        "status": row[4],
        "notes": row[5],
        "created_at": row[6],
        "updated_at": row[7],
    }


def _row_to_task(row: tuple) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "client_id": row[3],
        "deal_id": row[4],
        "is_completed": bool(row[5]),
        "due_date": row[6],
        "created_at": row[7],
        "updated_at": row[8],
    }


class CRMDatabase:
    """CRUD-операции для клиентов, сделок и задач. При инициализации создаёт таблицы, если их нет."""

    def __init__(self, db_path: str = "crm.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        with self._get_connection() as conn:
            for table_sql in ALL_TABLES:
                conn.execute(table_sql)
            conn.commit()

    # ---------- Клиенты ----------

    def client_create(self, name: str, email: Optional[str] = None, phone: Optional[str] = None,
                      status: str = "active", notes: Optional[str] = None) -> dict:
        now = _now_iso()
        with self._get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO clients (name, email, phone, status, notes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, email or None, phone or None, status, notes or None, now, now),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM clients WHERE id = ?", (cur.lastrowid,)).fetchone()
            return _row_to_client(tuple(row))

    def client_get(self, client_id: int) -> Optional[dict]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
            return _row_to_client(tuple(row)) if row else None

    def client_list(self, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> list[dict]:
        with self._get_connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM clients WHERE status = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                    (status, limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM clients ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)
                ).fetchall()
            return [_row_to_client(tuple(r)) for r in rows]

    def client_update(self, client_id: int, **kwargs) -> Optional[dict]:
        allowed = {"name", "email", "phone", "status", "notes"}
        optional_clear = {"email", "phone", "notes"}  # разрешить явную очистку (None)
        updates = {k: v for k, v in kwargs.items() if k in allowed and (v is not None or k in optional_clear)}
        if not updates:
            return self.client_get(client_id)
        updates["updated_at"] = _now_iso()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [client_id]
        with self._get_connection() as conn:
            conn.execute(f"UPDATE clients SET {set_clause} WHERE id = ?", params)
            conn.commit()
        return self.client_get(client_id)

    def client_delete(self, client_id: int) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            conn.commit()
            return cur.rowcount > 0

    def client_archive(self, client_id: int) -> Optional[dict]:
        return self.client_update(client_id, status="archived")

    def client_search(self, q: str, limit: int = 50) -> list[dict]:
        pattern = f"%{q}%"
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM clients
                   WHERE (name LIKE ? OR COALESCE(email, '') LIKE ? OR COALESCE(phone, '') LIKE ? OR COALESCE(notes, '') LIKE ?)
                   ORDER BY id DESC LIMIT ?""",
                (pattern, pattern, pattern, pattern, limit),
            ).fetchall()
            return [_row_to_client(tuple(r)) for r in rows]

    # ---------- Сделки ----------

    def deal_create(self, title: str, client_id: Optional[int] = None, amount: Optional[float] = None,
                    status: str = "draft", notes: Optional[str] = None) -> dict:
        now = _now_iso()
        with self._get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO deals (client_id, title, amount, status, notes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (client_id, title, amount, status, notes or None, now, now),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM deals WHERE id = ?", (cur.lastrowid,)).fetchone()
            return _row_to_deal(tuple(row))

    def deal_get(self, deal_id: int) -> Optional[dict]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
            return _row_to_deal(tuple(row)) if row else None

    def deal_list(self, client_id: Optional[int] = None, status: Optional[str] = None,
                  limit: int = 100, offset: int = 0) -> list[dict]:
        with self._get_connection() as conn:
            conditions, params = [], []
            if client_id is not None:
                conditions.append("client_id = ?")
                params.append(client_id)
            if status:
                conditions.append("status = ?")
                params.append(status)
            where = " WHERE " + " AND ".join(conditions) if conditions else ""
            params.extend([limit, offset])
            rows = conn.execute(
                f"SELECT * FROM deals{where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
            return [_row_to_deal(tuple(r)) for r in rows]

    def deal_update(self, deal_id: int, **kwargs) -> Optional[dict]:
        allowed = {"title", "client_id", "amount", "status", "notes"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return self.deal_get(deal_id)
        updates["updated_at"] = _now_iso()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [deal_id]
        with self._get_connection() as conn:
            conn.execute(f"UPDATE deals SET {set_clause} WHERE id = ?", params)
            conn.commit()
        return self.deal_get(deal_id)

    def deal_delete(self, deal_id: int) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
            conn.commit()
            return cur.rowcount > 0

    def deal_search(self, q: str, limit: int = 50) -> list[dict]:
        pattern = f"%{q}%"
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM deals
                   WHERE (title LIKE ? OR COALESCE(notes, '') LIKE ?)
                   ORDER BY id DESC LIMIT ?""",
                (pattern, pattern, limit),
            ).fetchall()
            return [_row_to_deal(tuple(r)) for r in rows]

    # ---------- Задачи ----------

    def task_create(self, title: str, description: Optional[str] = None, client_id: Optional[int] = None,
                    deal_id: Optional[int] = None, is_completed: bool = False,
                    due_date: Optional[str] = None) -> dict:
        now = _now_iso()
        with self._get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO tasks (title, description, client_id, deal_id, is_completed, due_date, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, description or None, client_id, deal_id, 1 if is_completed else 0, due_date, now, now),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
            return _row_to_task(tuple(row))

    def task_get(self, task_id: int) -> Optional[dict]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            return _row_to_task(tuple(row)) if row else None

    def task_list(self, client_id: Optional[int] = None, deal_id: Optional[int] = None,
                  is_completed: Optional[bool] = None, limit: int = 100, offset: int = 0) -> list[dict]:
        with self._get_connection() as conn:
            conditions, params = [], []
            if client_id is not None:
                conditions.append("client_id = ?")
                params.append(client_id)
            if deal_id is not None:
                conditions.append("deal_id = ?")
                params.append(deal_id)
            if is_completed is not None:
                conditions.append("is_completed = ?")
                params.append(1 if is_completed else 0)
            where = " WHERE " + " AND ".join(conditions) if conditions else ""
            params.extend([limit, offset])
            rows = conn.execute(
                f"SELECT * FROM tasks{where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
            return [_row_to_task(tuple(r)) for r in rows]

    def task_update(self, task_id: int, **kwargs) -> Optional[dict]:
        allowed = {"title", "description", "client_id", "deal_id", "is_completed", "due_date"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return self.task_get(task_id)
        if "is_completed" in updates:
            updates["is_completed"] = 1 if updates["is_completed"] else 0
        updates["updated_at"] = _now_iso()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [task_id]
        with self._get_connection() as conn:
            conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", params)
            conn.commit()
        return self.task_get(task_id)

    def task_delete(self, task_id: int) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cur.rowcount > 0

    def task_set_completed(self, task_id: int, completed: bool) -> Optional[dict]:
        return self.task_update(task_id, is_completed=completed)
