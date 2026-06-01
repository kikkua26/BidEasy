"""Pydantic 数据校验模型"""

from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, Field


# ═══════════════════════════════════
# 通用模型
# ═══════════════════════════════════

class ResponseModel(BaseModel):
    """统一响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[object] = None


class PaginatedResponse(BaseModel):
    """分页响应"""
    code: int = 0
    message: str = "success"
    data: dict = {"list": [], "total": 0, "page": 1, "page_size": 20}


# ═══════════════════════════════════
# 项目
# ═══════════════════════════════════

class ProjectCreate(BaseModel):
    """创建项目"""
    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    project_type: Optional[str] = Field(None, max_length=50, description="工程类型")
    project_scale: Optional[str] = Field(None, max_length=200, description="建设规模")
    bid_amount: Optional[Decimal] = Field(None, description="投标金额")
    project_info: Optional[str] = Field(None, description="项目概况")


class ProjectUpdate(BaseModel):
    """更新项目"""
    name: Optional[str] = None
    project_type: Optional[str] = None
    project_scale: Optional[str] = None
    bid_amount: Optional[Decimal] = None
    project_info: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    """项目响应"""
    id: str
    name: str
    project_type: Optional[str] = None
    project_scale: Optional[str] = None
    bid_amount: Optional[Decimal] = None
    project_info: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════
# 文档
# ═══════════════════════════════════

class DocumentResponse(BaseModel):
    """文档响应"""
    id: str
    project_id: str
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    content_type: Optional[str] = None
    raw_text: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentParseResult(BaseModel):
    """文档解析结果"""
    file_name: str
    file_type: str
    raw_text: str
    word_count: int
    page_count: Optional[int] = None


# ═══════════════════════════════════
# 评分点
# ═══════════════════════════════════

class ScoringCriteriaResponse(BaseModel):
    """评分点响应"""
    id: str
    project_id: str
    category: Optional[str] = None
    item_name: Optional[str] = None
    max_score: Optional[Decimal] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    sort_order: int

    model_config = {"from_attributes": True}


# ═══════════════════════════════════
# 大纲
# ═══════════════════════════════════

class OutlineNodeCreate(BaseModel):
    """创建大纲节点"""
    parent_id: Optional[str] = None
    level: int = Field(..., ge=1, le=4)
    title: str = Field(..., min_length=1, max_length=500)
    sort_order: int = 0


class OutlineNodeUpdate(BaseModel):
    """更新大纲节点"""
    title: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None


class OutlineNodeResponse(BaseModel):
    """大纲节点响应"""
    id: str
    project_id: str
    parent_id: Optional[str] = None
    level: int
    title: str
    sort_order: int
    status: str
    ai_suggested: bool
    children: Optional[list["OutlineNodeResponse"]] = None

    model_config = {"from_attributes": True}


class OutlineGenerateRequest(BaseModel):
    """AI生成大纲请求"""
    additional_requirements: Optional[str] = None


class OutlineChatRequest(BaseModel):
    """大纲对话调整请求"""
    message: str = Field(..., min_length=1, description="用户的修改意见")


# ═══════════════════════════════════
# 内容生成
# ═══════════════════════════════════

class SectionGenerateRequest(BaseModel):
    """生成章节内容请求"""
    outline_id: str
    additional_params: Optional[dict] = None


class SectionContentResponse(BaseModel):
    """章节内容响应"""
    id: str
    project_id: str
    outline_id: str
    content: Optional[str] = None
    word_count: int
    version: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════
# 审查
# ═══════════════════════════════════

class ReviewResponse(BaseModel):
    """审查记录响应"""
    id: str
    project_id: str
    outline_id: Optional[str] = None
    review_type: Optional[str] = None
    score: Optional[Decimal] = None
    feedback: Optional[str] = None
    suggestions: Optional[dict] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}
