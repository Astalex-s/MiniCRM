"""
Чтение и запись настроек Google (folder_id, credentials_path, client_secret_path) в JSON.
"""
import json
from pathlib import Path
from typing import Any, Dict

from ..config import GOOGLE_SETTINGS_PATH


def read_google_settings() -> Dict[str, Any]:
    if not GOOGLE_SETTINGS_PATH.exists():
        return {}
    try:
        with open(GOOGLE_SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_google_settings(data: Dict[str, Any]) -> None:
    GOOGLE_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GOOGLE_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
