"""系统设置 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.core.dependencies import get_db
from app.schemas import ResponseModel
from app.db.models import AppSetting

router = APIRouter(prefix="/api/v1/settings", tags=["系统设置"])

# ── 默认配置 ──
DEFAULTS = {
    "ai_api_key": "",
    "ai_base_url": "https://api.deepseek.com",
    "ai_model": "deepseek-chat",
    "ai_temperature": "0.7",
    "app_name": "奇易AI编标",
}


@router.get("", response_model=ResponseModel)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """获取所有设置"""
    result = await db.execute(select(AppSetting))
    rows = {row.key: row.value for row in result.scalars().all()}

    # 合并默认值
    settings = {}
    for key, default in DEFAULTS.items():
        settings[key] = rows.get(key, default)

    return ResponseModel(data=settings)


@router.put("", response_model=ResponseModel)
async def update_settings(body: dict, db: AsyncSession = Depends(get_db)):
    """更新设置"""
    for key, value in body.items():
        if key not in DEFAULTS:
            continue
        result = await db.execute(select(AppSetting).where(AppSetting.key == key))
        row = result.scalar_one_or_none()
        if row:
            row.value = str(value)
        else:
            db.add(AppSetting(key=key, value=str(value)))

    return ResponseModel(message="设置已保存")


@router.get("/ai", response_model=ResponseModel)
async def get_ai_settings(db: AsyncSession = Depends(get_db)):
    """获取 AI 配置（给服务层用）"""
    result = await db.execute(
        select(AppSetting).where(AppSetting.key.in_(["ai_api_key", "ai_base_url", "ai_model", "ai_temperature"]))
    )
    rows = {row.key: row.value for row in result.scalars().all()}
    return ResponseModel(data={
        "api_key": rows.get("ai_api_key", DEFAULTS["ai_api_key"]),
        "base_url": rows.get("ai_base_url", DEFAULTS["ai_base_url"]),
        "model": rows.get("ai_model", DEFAULTS["ai_model"]),
        "temperature": float(rows.get("ai_temperature", DEFAULTS["ai_temperature"])),
    })
