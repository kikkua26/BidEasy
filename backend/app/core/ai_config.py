"""动态 AI 配置（从数据库读取，fallback 到 .env）"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


async def get_ai_config(db: AsyncSession) -> dict:
    """从数据库读取 AI 配置，未设置则用 .env 默认值"""
    from app.db.models import AppSetting

    result = await db.execute(
        select(AppSetting).where(AppSetting.key.in_([
            "ai_api_key", "ai_base_url", "ai_model", "ai_temperature"
        ]))
    )
    rows = {row.key: row.value for row in result.scalars().all()}

    return {
        "api_key": rows.get("ai_api_key") or settings.OPENAI_API_KEY,
        "base_url": rows.get("ai_base_url") or settings.OPENAI_BASE_URL,
        "model": rows.get("ai_model") or settings.AI_MODEL,
        "temperature": float(rows.get("ai_temperature") or settings.AI_TEMPERATURE),
    }
