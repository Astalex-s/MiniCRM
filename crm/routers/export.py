"""API: экспорт в Google Таблицы и список отчётов."""
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from ..deps import get_db
from ..database import CRMDatabase
from ..services.export_service import export_to_google_sheet, list_export_files

router = APIRouter()


@router.post("/clients")
def export_clients(
    body: Dict[str, Any] = Body(default_factory=dict),
    db: CRMDatabase = Depends(get_db),
):
    folder_id = body.get("folder_id") if isinstance(body, dict) else None
    try:
        rows_data = sorted(db.client_list(limit=2000), key=lambda r: r["id"])
        headers = ["№", "ID", "Имя", "Email", "Телефон", "Статус", "Заметки", "Создан", "Обновлён"]

        def _escape_cell(v):
            """Экранировать значение для Excel/Sheets: + = - @ в начале трактуются как формула."""
            s = v if v is not None else ""
            s = str(s).strip()
            if s and s[0] in ("+", "=", "-", "@"):
                return "'" + str(v)
            return v if v is not None else ""

        rows = [
            [
                i + 1,
                r["id"], r["name"], r.get("email") or "", _escape_cell(r.get("phone")),
                r["status"], (r.get("notes") or "")[:500], r.get("created_at", ""), r.get("updated_at", ""),
            ]
            for i, r in enumerate(rows_data)
        ]
        return export_to_google_sheet(
            "CRM — Отчёт Клиенты", headers, rows, folder_id=folder_id,
            section="clients", rows_data=rows_data,
        )
    except Exception as e:
        from log import get_logger
        get_logger("crm.api").exception("Export clients: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deals")
def export_deals(
    body: Dict[str, Any] = Body(default_factory=dict),
    db: CRMDatabase = Depends(get_db),
):
    folder_id = body.get("folder_id") if isinstance(body, dict) else None
    try:
        rows_data = sorted(db.deal_list(limit=2000), key=lambda r: r["id"])
        headers = ["№", "ID", "Название", "ID клиента", "Сумма", "Статус", "Заметки", "Создан", "Обновлён"]
        rows = [
            [
                i + 1,
                r["id"], r["title"], r.get("client_id") or "", r.get("amount") or "",
                r["status"], (r.get("notes") or "")[:500], r.get("created_at", ""), r.get("updated_at", ""),
            ]
            for i, r in enumerate(rows_data)
        ]
        return export_to_google_sheet(
            "CRM — Отчёт Сделки", headers, rows, folder_id=folder_id,
            section="deals", rows_data=rows_data,
        )
    except Exception as e:
        from log import get_logger
        get_logger("crm.api").exception("Export deals: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks")
def export_tasks(
    body: Dict[str, Any] = Body(default_factory=dict),
    db: CRMDatabase = Depends(get_db),
):
    folder_id = body.get("folder_id") if isinstance(body, dict) else None
    try:
        rows_data = sorted(db.task_list(limit=2000), key=lambda r: r["id"])
        headers = ["№", "ID", "Название", "Описание", "ID клиента", "ID сделки", "Выполнено", "Срок", "Создан", "Обновлён"]
        rows = [
            [
                i + 1,
                r["id"], r["title"], (r.get("description") or "")[:500], r.get("client_id") or "", r.get("deal_id") or "",
                "Да" if r.get("is_completed") else "Нет", (r.get("due_date") or "")[:10], r.get("created_at", ""), r.get("updated_at", ""),
            ]
            for i, r in enumerate(rows_data)
        ]
        return export_to_google_sheet(
            "CRM — Отчёт Задачи", headers, rows, folder_id=folder_id,
            section="tasks", rows_data=rows_data,
        )
    except Exception as e:
        from log import get_logger
        get_logger("crm.api").exception("Export tasks: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
def list_files(section: str = Query(..., description="clients, deals или tasks")):
    try:
        items = list_export_files(section)
        return {"section": section, "files": items}
    except Exception as e:
        from log import get_logger
        get_logger("crm.api").exception("List export files: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
