"""数据库模型"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text,
    DateTime, ForeignKey, JSON, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.utcnow()


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False, comment="项目名称")
    project_type = Column(String(50), comment="工程类型")
    project_scale = Column(String(200), comment="建设规模")
    bid_amount = Column(DECIMAL(15, 2), comment="投标金额")
    project_info = Column(Text, comment="项目概况信息")
    status = Column(String(20), default="draft", comment="状态: draft/in_progress/completed")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # 关联
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    scoring_criteria = relationship("ScoringCriteria", back_populates="project", cascade="all, delete-orphan")
    outlines = relationship("OutlineNode", back_populates="project", cascade="all, delete-orphan")
    section_contents = relationship("SectionContent", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    """招文文档表"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(200))
    file_type = Column(String(20), comment="pdf / docx / text")
    content_type = Column(String(50), comment="招标公告 / 投标须知 / 合同条款 / 技术规范 / 其他")
    raw_text = Column(Text, comment="提取的原始文本")
    parsed_content = Column(JSON, comment="结构化解析结果")
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="documents")


class ScoringCriteria(Base):
    """评分点表"""
    __tablename__ = "scoring_criteria"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(100), comment="评分类别")
    item_name = Column(String(200), comment="评分项名称")
    max_score = Column(DECIMAL(5, 2), comment="满分值")
    description = Column(Text, comment="评分标准描述")
    requirements = Column(Text, comment="具体要求")
    sort_order = Column(Integer, default=0)

    project = relationship("Project", back_populates="scoring_criteria")


class OutlineNode(Base):
    """大纲节点表"""
    __tablename__ = "outline_nodes"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=False), ForeignKey("outline_nodes.id", ondelete="CASCADE"), nullable=True)
    level = Column(Integer, nullable=False, comment="层级 1-4")
    title = Column(String(500), nullable=False, comment="章节标题")
    sort_order = Column(Integer, default=0)
    status = Column(String(20), default="draft", comment="draft / confirmed / locked")
    ai_suggested = Column(Boolean, default=False, comment="是否AI建议")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    project = relationship("Project", back_populates="outlines")
    parent = relationship("OutlineNode", remote_side=[id], backref="children")
    contents = relationship("SectionContent", back_populates="outline_node", cascade="all, delete-orphan")


class SectionContent(Base):
    """章节内容表"""
    __tablename__ = "section_contents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    outline_id = Column(UUID(as_uuid=False), ForeignKey("outline_nodes.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, comment="生成的内容")
    word_count = Column(Integer, default=0)
    version = Column(Integer, default=1)
    status = Column(String(20), default="generated", comment="generated / reviewed / approved")
    generation_params = Column(JSON, comment="生成参数")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    project = relationship("Project", back_populates="section_contents")
    outline_node = relationship("OutlineNode", back_populates="contents")


class Review(Base):
    """审查记录表"""
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    outline_id = Column(UUID(as_uuid=False), ForeignKey("outline_nodes.id", ondelete="SET NULL"), nullable=True)
    review_type = Column(String(50), comment="scoring / completeness / quality")
    score = Column(DECIMAL(5, 2))
    feedback = Column(Text)
    suggestions = Column(JSON, comment="修改建议")
    status = Column(String(20), comment="pass / revise")
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="reviews")


class SolutionLibrary(Base):
    """方案库表（预留后期实现）"""
    __tablename__ = "solution_library"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    category = Column(String(100), comment="方案类别")
    project_type = Column(String(50), comment="适用工程类型")
    title = Column(String(500), nullable=False)
    content = Column(Text)
    tags = Column(JSON, default=list)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
