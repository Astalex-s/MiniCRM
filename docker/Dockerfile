# FastAPI CRM backend. Режим разработки: код монтируется, uvicorn --reload (watchfiles).
FROM python:3.11-slim

WORKDIR /app

# Зависимости: uvicorn[standard] включает watchfiles для --reload
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код копируется при сборке; при запуске через Compose монтируется поверх (volume)
COPY . .

EXPOSE 8000

# Watchdog: --reload перезапускает приложение при изменении файлов в смонтированном коде
CMD ["uvicorn", "crm.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
