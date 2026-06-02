"""动态 AI 配置（从数据库读取，fallback 到 .env）"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


async def get_ai_config(db: AsyncSession) -> dict:
    """从数据库读取 AI 配置，未设置则用 .env 默认值

    返回：
        api_key, base_url, model, temperature, extra_headers
    """
    from app.db.models import AppSetting

    result = await db.execute(
        select(AppSetting).where(AppSetting.key.in_([
            "ai_api_key", "ai_base_url", "ai_model", "ai_temperature"
        ]))
    )
    rows = {row.key: row.value for row in result.scalars().all()}

    api_key = rows.get("ai_api_key") or settings.OPENAI_API_KEY
    base_url = rows.get("ai_base_url") or settings.OPENAI_BASE_URL

    # MiMo Token Plan 使用 api-key header（格式 tp-xxx）
    extra_headers = {}
    if api_key.startswith("tp-"):
        extra_headers["api-key"] = api_key

    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": rows.get("ai_model") or settings.AI_MODEL,
        "temperature": float(rows.get("ai_temperature") or settings.AI_TEMPERATURE),
        "extra_headers": extra_headers,
    }
