"""FastAPI 应用入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时：初始化数据库
    if settings.DEBUG:
        await init_db()
    yield
    # 关闭时：清理资源


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="施工行业技术标AI编标系统",
    lifespan=lifespan,
)

# ── CORS 配置 ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 注册路由 ──
from app.api.v1 import api_router
app.include_router(api_router)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
