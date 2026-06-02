"""API v1 路由汇总"""

from fastapi import APIRouter

from app.api.v1.projects import router as projects_router
from app.api.v1.documents import router as documents_router
from app.api.v1.outline import router as outline_router
from app.api.v1.generate import router as generate_router
from app.api.v1.settings import router as settings_router

api_router = APIRouter()

api_router.include_router(projects_router)
api_router.include_router(documents_router)
api_router.include_router(outline_router)
api_router.include_router(generate_router)
api_router.include_router(settings_router)
