"""数据库模型（兼容 SQLite 和 PostgreSQL）"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text,
    DateTime, ForeignKey, JSON, DECIMAL
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── 统一的 ID 类型：SQLite 用 String(36)，PostgreSQL 用 UUID ──
def pk_column():
    """主键列"""
    return Column(String(36), primary_key=True, default=gen_uuid)


def fk_column(target: str, ondelete: str | None = None, nullable: bool = False):
    """外键列"""
    fk_kwargs = {}
    if ondelete:
        fk_kwargs["ondelete"] = ondelete
    return Column(String(36), ForeignKey(target, **fk_kwargs), nullable=nullable)


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = pk_column()
    name = Column(String(200), nullable=False)
    project_type = Column(String(50))
    project_scale = Column(String(200))
    bid_amount = Column(DECIMAL(15, 2))
    project_info = Column(Text)
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    scoring_criteria = relationship("ScoringCriteria", back_populates="project", cascade="all, delete-orphan")
    outlines = relationship("OutlineNode", back_populates="project", cascade="all, delete-orphan")
    section_contents = relationship("SectionContent", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    """招文文档表"""
    __tablename__ = "documents"

    id = pk_column()
    project_id = fk_column("projects.id", ondelete="CASCADE", nullable=False)
    file_name = Column(String(200))
    file_type = Column(String(20))
    content_type = Column(String(50))
    raw_text = Column(Text)
    parsed_content = Column(JSON)
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="documents")


class ScoringCriteria(Base):
    """评分点表"""
    __tablename__ = "scoring_criteria"

    id = pk_column()
    project_id = fk_column("projects.id", ondelete="CASCADE", nullable=False)
    category = Column(String(100))
    item_name = Column(String(200))
    max_score = Column(DECIMAL(5, 2))
    description = Column(Text)
    requirements = Column(Text)
    sort_order = Column(Integer, default=0)

    project = relationship("Project", back_populates="scoring_criteria")


class OutlineNode(Base):
    """大纲节点表"""
    __tablename__ = "outline_nodes"

    id = pk_column()
    project_id = fk_column("projects.id", ondelete="CASCADE", nullable=False)
    parent_id = fk_column("outline_nodes.id", ondelete="CASCADE", nullable=True)
    level = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0)
    status = Column(String(20), default="draft")
    ai_suggested = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    project = relationship("Project", back_populates="outlines")
    parent = relationship("OutlineNode", remote_side=[id], backref="children")
    contents = relationship("SectionContent", back_populates="outline_node", cascade="all, delete-orphan")


class SectionContent(Base):
    """章节内容表"""
    __tablename__ = "section_contents"

    id = pk_column()
    project_id = fk_column("projects.id", ondelete="CASCADE", nullable=False)
    outline_id = fk_column("outline_nodes.id", ondelete="CASCADE", nullable=False)
    content = Column(Text)
    word_count = Column(Integer, default=0)
    version = Column(Integer, default=1)
    status = Column(String(20), default="generated")
    generation_params = Column(JSON)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    project = relationship("Project", back_populates="section_contents")
    outline_node = relationship("OutlineNode", back_populates="contents")


class Review(Base):
    """审查记录表"""
    __tablename__ = "reviews"

    id = pk_column()
    project_id = fk_column("projects.id", ondelete="CASCADE", nullable=False)
    outline_id = fk_column("outline_nodes.id", ondelete="SET NULL", nullable=True)
    review_type = Column(String(50))
    score = Column(DECIMAL(5, 2))
    feedback = Column(Text)
    suggestions = Column(JSON)
    status = Column(String(20))
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="reviews")


class AppSetting(Base):
    """系统设置表（key-value）"""
    __tablename__ = "app_settings"

    id = pk_column()
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class SolutionLibrary(Base):
    """方案库表（预留）"""
    __tablename__ = "solution_library"

    id = pk_column()
    category = Column(String(100))
    project_type = Column(String(50))
    title = Column(String(500), nullable=False)
    content = Column(Text)
    tags = Column(JSON, default=list)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
