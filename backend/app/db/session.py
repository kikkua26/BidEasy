"""数据库引擎和会话管理"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# 连接超时参数（开发模式下无 PostgreSQL 时快速返回）
connect_args = {
    "timeout": 3,          # 连接超时 3 秒
    "command_timeout": 5,  # 命令超时 5 秒
}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    connect_args=connect_args,
    pool_recycle=300,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""
    pass


async def get_db() -> AsyncSession:
    """获取数据库会话（依赖注入）"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库（创建所有表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
