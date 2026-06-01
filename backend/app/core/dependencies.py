"""公共依赖注入"""

import logging
from typing import AsyncGenerator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory

logger = logging.getLogger("uvicorn")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """数据库会话依赖"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.exception(f"DB异常: {e}")
            raise HTTPException(status_code=500, detail=str(e))
