"""
Точка входа: запуск веб-интерфейса мини-CRM (React, Vite).
Поднимает dev-сервер фронтенда и открывает браузер на http://localhost:5173
Бэкенд должен быть запущен отдельно: uvicorn crm.main:app --reload
"""
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"

def main():
    if not (FRONTEND / "package.json").exists():
        print("Папка frontend не найдена или не установлены зависимости. Выполните: cd frontend && npm install")
        sys.exit(1)
    print("Запуск веб-интерфейса CRM на http://localhost:5173")
    print("Бэкенд должен быть запущен: uvicorn crm.main:app --reload")
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    time.sleep(2)
    webbrowser.open("http://localhost:5173")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
