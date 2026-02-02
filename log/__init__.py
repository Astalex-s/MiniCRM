"""
Настройка логирования. Все логи пишутся в папку logs/ в корне проекта.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Папка для лог-файлов: корень проекта / logs
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = _PROJECT_ROOT / "logs"

# Имя основного лог-файла
APP_LOG_NAME = "app.log"
CRM_LOG_NAME = "crm.log"
GUI_LOG_NAME = "gui.log"

_FORMAT_FILE = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_FORMAT_CONSOLE = "%(levelname)-8s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _ensure_logs_dir():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(
    level=logging.INFO,
    log_file=APP_LOG_NAME,
    max_bytes=2 * 1024 * 1024,
    backup_count=3,
    console=True,
):
    """
    Настраивает логирование: файл в logs/ и опционально консоль.
    Вызывать при старте приложения (бэкенд или GUI).
    """
    _ensure_logs_dir()
    log_path = LOGS_DIR / log_file
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(level)
    formatter_file = logging.Formatter(_FORMAT_FILE, datefmt=_DATE_FMT)
    formatter_console = logging.Formatter(_FORMAT_CONSOLE, datefmt=_DATE_FMT)
    fh = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    fh.setLevel(level)
    fh.setFormatter(formatter_file)
    root.addHandler(fh)
    if console:
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(level)
        ch.setFormatter(formatter_console)
        root.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    """Возвращает логгер с указанным именем (например, 'crm.api', 'gui.api')."""
    return logging.getLogger(name)
