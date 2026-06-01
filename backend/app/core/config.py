"""应用核心配置"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # ── 应用 ──
    APP_NAME: str = "奇易AI编标"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # ── 数据库 ──
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/qiyi_ai_bid"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/qiyi_ai_bid"

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
