# Docker: CRM API (FastAPI)

## Одна команда для запуска

Из **корня проекта** (EXCELIO):

```powershell
docker compose -f docker/docker-compose.yml up --build
```

Или через скрипт (из любой папки, скрипт сам перейдёт в корень):

```powershell
.\docker\run.ps1
```

Для фонового режима: `docker compose -f docker/docker-compose.yml up --build -d`

## Что настроено

- **Dockerfile** — образ на Python 3.11, установка зависимостей, `uvicorn crm.main:app --reload --host 0.0.0.0`.
- **docker-compose.yml** — сборка из корня проекта, порт 8000, **монтирование кода** (`..:/app`): правки на хосте сразу попадают в контейнер.
- **Watchdog** — `uvicorn --reload` (через `uvicorn[standard]` / watchfiles) перезапускает приложение при изменении файлов. Контейнер и Compose перезапускать не нужно.

## Остановка

`Ctrl+C` в терминале или в другом окне:

```powershell
docker compose -f docker/docker-compose.yml down
```

API после запуска: http://localhost:8000, документация: http://localhost:8000/docs
