"""FastAPI 应用入口"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger("uvicorn")


# ── CORS 中间件（确保错误响应也有 CORS 头）──
class ForceCORSMiddleware(BaseHTTPMiddleware):
    """确保所有响应（包括500错误）都有 CORS 头部"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception:
            # 捕获未处理异常，返回带 CORS 头的 500
            return JSONResponse(
                status_code=500,
                content={"code": 50001, "message": "服务器内部错误", "data": None},
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*",
                },
            )

        # 确保所有响应都有 CORS 头
        if "Access-Control-Allow-Origin" not in response.headers:
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    if settings.DEBUG:
        try:
            from app.db.session import init_db
            await init_db()
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.warning(f"数据库未连接: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="施工行业技术标AI编标系统",
    lifespan=lifespan,
)

# ── CORS 配置 ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 兜底 CORS 中间件
app.add_middleware(ForceCORSMiddleware)


# ── 全局异常处理 ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理，确保返回带 CORS 头的 JSON"""
    logger.exception(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"code": 50001, "message": f"服务器内部错误: {str(exc)}", "data": None},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


# ── 注册路由 ──
from app.api.v1 import api_router
app.include_router(api_router)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
