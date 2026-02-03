"""
Зависимости FastAPI: экземпляр БД и т.д.
"""
from typing import Optional

from .config import DB_PATH
from .database import CRMDatabase

_db: Optional[CRMDatabase] = None


def get_db() -> CRMDatabase:
    global _db
    if _db is None:
        _db = CRMDatabase(str(DB_PATH))
    return _db
