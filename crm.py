"""
Точка входа: запуск визуального интерфейса мини-CRM (Tkinter).
Перед запуском убедитесь, что бэкенд запущен: uvicorn crm.main:app --reload
"""
import sys
from pathlib import Path

# Корень проекта в path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gui.crm_gui import main

if __name__ == "__main__":
    main()
