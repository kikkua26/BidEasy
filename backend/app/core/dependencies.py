"""公共依赖注入"""

import asyncio
import logging
from typing import AsyncGenerator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("uvicorn")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """数据库会话依赖（超时快速失败）"""
    try:
        from app.db.session import async_session_factory

        # 5秒内必须连上，否则快速失败
        async with asyncio.timeout(6):
            async with async_session_factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    logger.warning(f"数据库操作失败: {e}")
                    raise HTTPException(
                        status_code=503,
                        detail="数据库服务不可用，请先启动 PostgreSQL",
                    )
                finally:
                    await session.close()
    except asyncio.TimeoutError:
        logger.warning("数据库连接超时")
        raise HTTPException(
            status_code=503,
            detail="数据库连接超时，请确认 PostgreSQL 已启动",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"数据库不可用: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"数据库不可用: {str(e)}",
        )
