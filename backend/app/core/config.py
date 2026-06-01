"""应用核心配置"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # ── 应用 ──
    APP_NAME: str = "奇易AI编标"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # ── 数据库（默认 SQLite，生产环境设 DATABASE_URL=postgresql+asyncpg://...）──
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/qiyi_ai_bid.db"
    DATABASE_URL_SYNC: str = "sqlite:///./data/qiyi_ai_bid.db"

    # ── AI 服务 ──
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o"
    AI_TEMPERATURE: float = 0.7

    # ── 文件存储 ──
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ── 服务 ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 确保数据目录存在
os.makedirs(os.path.dirname(settings.DATABASE_URL.split("///")[-1] if "///" in settings.DATABASE_URL else "./data"), exist_ok=True)
