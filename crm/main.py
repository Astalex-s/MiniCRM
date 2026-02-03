"""
FastAPI-бэкенд мини-CRM.
Эндпоинты для клиентов, сделок и задач, экспорт в Google Таблицы.
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, Query, Request, Body, UploadFile
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

# Файл БД и настройки Google
DB_PATH = Path(__file__).resolve().parent.parent / "crm.db"
_ROOT = Path(__file__).resolve().parent.parent
GOOGLE_SETTINGS_PATH = _ROOT / "config" / "google_export_settings.json"

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


# ---------- Настройки Google (сохраняются в файл) ----------

def _read_google_settings() -> Dict[str, Any]:
    if not GOOGLE_SETTINGS_PATH.exists():
        return {}
    try:
        with open(GOOGLE_SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_google_settings(data: Dict[str, Any]) -> None:
    GOOGLE_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GOOGLE_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.get("/settings/google")
def get_google_settings():
    """Настройки Google для экспорта (folder_id, пути к JSON и т.д.)."""
    return _read_google_settings()


@app.post("/settings/google")
def save_google_settings(payload: Dict[str, Any] = Body(...)):
    """Сохранить настройки Google в файл (folder_id, credentials_path и т.д.)."""
    allowed = {"folder_id", "credentials_path", "client_secret_path"}
    data = _read_google_settings()
    data.update({k: v for k, v in payload.items() if k in allowed and v is not None})
    _write_google_settings(data)
    return data


CONFIG_DIR = _ROOT / "config"
# Сервисный аккаунт сохраняем как excel-factory.json (интеграция ищет *excel-factory*.json)
ALLOWED_UPLOAD_NAMES = {"credentials": "excel-factory.json", "client_secret": "client_secret.json"}


@app.post("/settings/google/upload")
async def upload_google_settings_file(
    file: UploadFile = File(...),
    target: str = Query(..., description="credentials или client_secret"),
):
    """Загрузить JSON конфигурации в config/ и вернуть путь для настроек."""
    if target not in ALLOWED_UPLOAD_NAMES:
        raise HTTPException(status_code=400, detail="target должен быть credentials или client_secret")
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Нужен файл с расширением .json")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    save_name = ALLOWED_UPLOAD_NAMES[target]
    save_path = CONFIG_DIR / save_name
    try:
        content = await file.read()
        save_path.write_bytes(content)
    except Exception as e:
        logger.exception("Upload settings file: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    relative_path = f"config/{save_name}"
    return {"path": relative_path}


# ---------- Экспорт в Google Таблицы ----------

def _col_letter(n: int) -> str:
    """Номер столбца (1-based) в букву A, B, ..., Z, AA, ..."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s or "A"


def _resolve_creds_path(path: Optional[str]) -> Optional[str]:
    """Путь к credentials: если относительный — от корня проекта."""
    if not path or Path(path).is_absolute():
        return path
    return str(_ROOT / path.replace("\\", "/"))


def _get_service_account_email(credentials_path: str) -> str:
    """Из JSON ключа сервисного аккаунта достаёт client_email."""
    p = Path(credentials_path)
    if not p.is_absolute():
        p = _ROOT / credentials_path.replace("\\", "/")
    data = json.loads(p.read_text(encoding="utf-8"))
    return data.get("client_email") or ""


def _export_to_google_sheet(
    title: str,
    headers: List[str],
    rows: List[List[Any]],
    folder_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Создаёт Google Таблицу (как в main() google_drive_client: OAuth пользователя, квота в его Drive),
    название = раздел + timestamp. Затем записывает данные через Sheets API.
    """
    from integrations.google_drive_client import GoogleDriveClient, GoogleDriveUserClient, MIME_GOOGLE_SHEET
    from integrations.google_sheets_client import GoogleSheetsClient

    settings = _read_google_settings()
    creds_path = _resolve_creds_path(settings.get("credentials_path"))
    client_secret_path = _resolve_creds_path(settings.get("client_secret_path"))
    fid = folder_id or settings.get("folder_id")

    # Название файла: раздел + timestamp (как в main — создание от имени пользователя)
    title_with_ts = f"{title} {datetime.now().strftime('%Y-%m-%d %H-%M-%S')}"

    if client_secret_path:
        # OAuth пользователя: файл в его Drive, его квота (как в main())
        drive_user = GoogleDriveUserClient(client_secret_path=client_secret_path)
        meta = drive_user.create_google_sheet(title=title_with_ts, folder_id=fid or None)
        spreadsheet_id = meta["id"]
        web_view_link = meta.get("webViewLink", "")
        # Даём доступ сервисному аккаунту для записи данных
        if creds_path:
            sa_email = _get_service_account_email(creds_path)
            if sa_email:
                drive_user.share_file_with_email(spreadsheet_id, sa_email, role="writer")
    else:
        # Fallback: сервисный аккаунт (как раньше)
        drive = GoogleDriveClient(credentials_path=creds_path)
        meta = drive.create_file(title_with_ts, MIME_GOOGLE_SHEET, folder_id=fid or None)
        spreadsheet_id = meta["id"]
        web_view_link = meta.get("webViewLink", "")

    sheets = GoogleSheetsClient(spreadsheet_id=spreadsheet_id, credentials_path=creds_path)
    sheet_name = sheets.get_sheet_titles()[0]
    values = [headers] + [[str(c) for c in row] for row in rows]
    num_rows, num_cols = len(values), len(headers)
    range_name = f"A1:{_col_letter(num_cols)}{num_rows}"
    sheets.write_range(
        range_name=range_name,
        values=values,
        sheet_name=sheet_name,
        value_input_option="USER_ENTERED",
    )
    sheets.format_range_header(
        sheet_name=sheet_name,
        start_row=0,
        end_row=1,
        start_column=0,
        end_column=num_cols,
    )

    return {"spreadsheet_id": spreadsheet_id, "webViewLink": web_view_link, "title": title_with_ts}


@app.post("/export/clients")
def export_clients(body: Dict[str, Any] = Body(default_factory=dict)):
    """Выгрузить список клиентов в новую Google Таблицу."""
    folder_id = body.get("folder_id") if isinstance(body, dict) else None
    try:
        rows_data = db.client_list(limit=2000)
        headers = ["ID", "Имя", "Email", "Телефон", "Статус", "Заметки", "Создан", "Обновлён"]
        rows = [
            [r["id"], r["name"], r.get("email") or "", r.get("phone") or "", r["status"], (r.get("notes") or "")[:500], r.get("created_at", ""), r.get("updated_at", "")]
            for r in rows_data
        ]
        return _export_to_google_sheet("CRM — Отчёт Клиенты", headers, rows, folder_id=folder_id)
    except Exception as e:
        logger.exception("Export clients: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/deals")
def export_deals(body: Dict[str, Any] = Body(default_factory=dict)):
    """Выгрузить список сделок в новую Google Таблицу."""
    folder_id = body.get("folder_id") if isinstance(body, dict) else None
    try:
        rows_data = db.deal_list(limit=2000)
        headers = ["ID", "Название", "ID клиента", "Сумма", "Статус", "Заметки", "Создан", "Обновлён"]
        rows = [
            [r["id"], r["title"], r.get("client_id") or "", r.get("amount") or "", r["status"], (r.get("notes") or "")[:500], r.get("created_at", ""), r.get("updated_at", "")]
            for r in rows_data
        ]
        return _export_to_google_sheet("CRM — Отчёт Сделки", headers, rows, folder_id=folder_id)
    except Exception as e:
        logger.exception("Export deals: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/tasks")
def export_tasks(body: Dict[str, Any] = Body(default_factory=dict)):
    """Выгрузить список задач в новую Google Таблицу."""
    folder_id = body.get("folder_id") if isinstance(body, dict) else None
    try:
        rows_data = db.task_list(limit=2000)
        headers = ["ID", "Название", "Описание", "ID клиента", "ID сделки", "Выполнено", "Срок", "Создан", "Обновлён"]
        rows = [
            [
                r["id"], r["title"], (r.get("description") or "")[:500], r.get("client_id") or "", r.get("deal_id") or "",
                "Да" if r.get("is_completed") else "Нет", (r.get("due_date") or "")[:10], r.get("created_at", ""), r.get("updated_at", ""),
            ]
            for r in rows_data
        ]
        return _export_to_google_sheet("CRM — Отчёт Задачи", headers, rows, folder_id=folder_id)
    except Exception as e:
        logger.exception("Export tasks: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


SECTION_PREFIXES = {
    "clients": "CRM — Отчёт Клиенты",
    "deals": "CRM — Отчёт Сделки",
    "tasks": "CRM — Отчёт Задачи",
}


def _list_export_files(section: str) -> List[Dict[str, Any]]:
    """Список отчётов в папке Drive по разделу (clients/deals/tasks)."""
    from integrations.google_drive_client import GoogleDriveClient, GoogleDriveUserClient

    settings = _read_google_settings()
    creds_path = _resolve_creds_path(settings.get("credentials_path"))
    client_secret_path = _resolve_creds_path(settings.get("client_secret_path"))
    fid = settings.get("folder_id")
    prefix = SECTION_PREFIXES.get(section)
    if not prefix:
        return []

    if client_secret_path:
        client = GoogleDriveUserClient(client_secret_path=client_secret_path)
    else:
        client = GoogleDriveClient(credentials_path=creds_path)

    q = "trashed = false and mimeType = 'application/vnd.google-apps.spreadsheet'"
    if fid and fid != "root":
        q += f" and '{fid}' in parents"
    else:
        q += " and 'root' in parents"

    result = (
        client._service.files()
        .list(
            q=q,
            pageSize=100,
            orderBy="modifiedTime desc",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)",
        )
        .execute()
    )
    files = result.get("files", [])
    out = [f for f in files if (f.get("name") or "").startswith(prefix)]
    return [{"id": f["id"], "name": f["name"], "webViewLink": f.get("webViewLink", ""), "modifiedTime": f.get("modifiedTime", "")} for f in out]


@app.get("/export/files")
def list_export_files(section: str = Query(..., description="clients, deals или tasks")):
    """Список выгруженных отчётов в Google Drive по разделу."""
    try:
        items = _list_export_files(section)
        return {"section": section, "files": items}
    except Exception as e:
        logger.exception("List export files: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
