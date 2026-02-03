"""
Конфигурация CRM: пути к БД, настройкам Google, корень проекта.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "crm.db"
CONFIG_DIR = ROOT / "config"
GOOGLE_SETTINGS_PATH = CONFIG_DIR / "google_export_settings.json"

ALLOWED_UPLOAD_NAMES = {"credentials": "excel-factory.json", "client_secret": "client_secret.json"}

SECTION_PREFIXES = {
    "clients": "CRM — Отчёт Клиенты",
    "deals": "CRM — Отчёт Сделки",
    "tasks": "CRM — Отчёт Задачи",
}
