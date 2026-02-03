from fastapi import APIRouter

from .clients import router as clients_router
from .deals import router as deals_router
from .tasks import router as tasks_router
from .settings import router as settings_router
from .export import router as export_router

api_router = APIRouter()
api_router.include_router(clients_router, prefix="/clients", tags=["clients"])
api_router.include_router(deals_router, prefix="/deals", tags=["deals"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(export_router, prefix="/export", tags=["export"])
