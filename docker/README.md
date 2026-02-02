# Docker: CRM (API + веб-интерфейс)

## Одна команда: контейнеры + браузер

Из **корня проекта** (EXCELIO):

```powershell
.\docker\run.ps1
```

Скрипт:
1. Собирает и запускает контейнеры **crm-api** (порт 8000) и **crm-frontend** (порт 5173).
2. Ждёт готовности фронтенда (до ~45 сек).
3. Открывает в браузере **http://localhost:5173**.

Требуется запущенный **Docker Engine**.

## Вручную

```powershell
cd D:\MyStudy\ZEROCODER\PROJECTS\EXCELIO
docker compose -f docker/docker-compose.yml up --build -d
```

После запуска откройте в браузере: http://localhost:5173

## Сервисы

| Сервис        | Порт | Описание                    |
|---------------|------|-----------------------------|
| **crm-api**   | 8000 | FastAPI, SQLite, монтирование кода, `--reload` |
| **crm-frontend** | 5173 | React (Vite), прокси `/api` → crm-api:8000     |

## Остановка

```powershell
docker compose -f docker/docker-compose.yml down
```

API: http://localhost:8000  
Документация API: http://localhost:8000/docs
