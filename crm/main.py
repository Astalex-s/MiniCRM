"""
FastAPI-бэкенд мини-CRM.
Точка входа: создание приложения, CORS, middleware, подключение роутеров.
"""
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import DB_PATH
from .routers import api_router

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from log import setup_logging, get_logger

setup_logging(log_file="crm.log", console=True)
logger = get_logger("crm.api")

app = FastAPI(title="Mini CRM API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    method, path = request.method, request.url.path
    logger.info("Request: %s %s", method, path)
    try:
        response = await call_next(request)
        logger.info("Response: %s %s -> %s", method, path, response.status_code)
        return response
    except Exception as e:
        logger.exception("Error handling %s %s: %s", method, path, e)
        raise


app.include_router(api_router)


@app.get("/")
def root():
    return {
        "app": "Mini CRM API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def startup():
    logger.info("CRM API started, DB: %s", DB_PATH)
