"""API: настройки Google (чтение/запись, загрузка файлов конфигурации)."""
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from ..config import CONFIG_DIR, ALLOWED_UPLOAD_NAMES
from ..services.google_settings import read_google_settings, write_google_settings

router = APIRouter()


@router.get("/google")
def get_google_settings():
    return read_google_settings()


@router.post("/google")
def save_google_settings(payload: Dict[str, Any]):
    allowed = {"folder_id", "credentials_path", "client_secret_path"}
    data = read_google_settings()
    data.update({k: v for k, v in payload.items() if k in allowed and v is not None})
    write_google_settings(data)
    return data


@router.post("/google/upload")
async def upload_google_settings_file(
    file: UploadFile = File(...),
    target: str = Query(..., description="credentials или client_secret"),
):
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
        from log import get_logger
        get_logger("crm.api").exception("Upload settings file: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    return {"path": f"config/{save_name}"}
