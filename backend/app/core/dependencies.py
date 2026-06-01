"""公共依赖注入"""

import logging
from typing import AsyncGenerator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("uvicorn")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """数据库会话依赖"""
    from app.db.session import async_session_factory

    try:
        async with async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.exception(f"DB 操作异常: {e}")
                raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(e)}")
            finally:
                await session.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"DB 连接异常: {e}")
        raise HTTPException(status_code=503, detail=f"数据库不可用: {str(e)}")
