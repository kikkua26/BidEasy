"""公共依赖注入"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """数据库会话依赖"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
