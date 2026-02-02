"""Мини-CRM: модели, БД, API."""
from .database import CRMDatabase
from .models import Client, Deal, Task

__all__ = ["CRMDatabase", "Client", "Deal", "Task"]
