"""大纲管理 API"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger("uvicorn")

from app.core.dependencies import get_db
from app.schemas import (
    ResponseModel,
    OutlineNodeCreate,
    OutlineNodeUpdate,
    OutlineNodeResponse,
    OutlineGenerateRequest,
    OutlineChatRequest,
)
from app.db.models import OutlineNode, Project, Document

router = APIRouter(prefix="/api/v1/projects/{project_id}/outline", tags=["大纲管理"])


async def _get_project(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def _build_outline_tree(nodes: list[OutlineNode], parent_id: str | None = None) -> list[dict]:
    """构建大纲树结构"""
    tree = []
    children = [n for n in nodes if n.parent_id == parent_id]
    children.sort(key=lambda x: x.sort_order)
    for node in children:
        item = OutlineNodeResponse.model_validate(node).model_dump()
        item["children"] = _build_outline_tree(nodes, node.id)
        tree.append(item)
    return tree


@router.get("", response_model=ResponseModel)
async def get_outline(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取大纲树"""
    await _get_project(project_id, db)
    result = await db.execute(
        select(OutlineNode).where(OutlineNode.project_id == project_id).order_by(OutlineNode.sort_order)
    )
    nodes = list(result.scalars().all())
    tree = _build_outline_tree(nodes)
    return ResponseModel(data=tree)


@router.post("/nodes", response_model=ResponseModel)
async def create_node(
    project_id: str,
    body: OutlineNodeCreate,
    db: AsyncSession = Depends(get_db),
):
    """添加大纲节点"""
    await _get_project(project_id, db)

    if body.level > 4:
        raise HTTPException(status_code=400, detail="大纲层级不超过4层")

    node = OutlineNode(
        project_id=project_id,
        parent_id=body.parent_id,
        level=body.level,
        title=body.title,
        sort_order=body.sort_order,
    )
    db.add(node)
    await db.flush()
    return ResponseModel(data=OutlineNodeResponse.model_validate(node))


@router.put("/nodes/{node_id}", response_model=ResponseModel)
async def update_node(
    project_id: str,
    node_id: str,
    body: OutlineNodeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新大纲节点"""
    result = await db.execute(
        select(OutlineNode).where(OutlineNode.id == node_id, OutlineNode.project_id == project_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(node, key, value)
    await db.flush()
    return ResponseModel(data=OutlineNodeResponse.model_validate(node))


@router.delete("/nodes/{node_id}", response_model=ResponseModel)
async def delete_node(
    project_id: str,
    node_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除大纲节点（级联删除子节点）"""
    result = await db.execute(
        select(OutlineNode).where(OutlineNode.id == node_id, OutlineNode.project_id == project_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    # 递归查找并删除所有子孙节点
    async def collect_descendants(parent_id: str) -> list[OutlineNode]:
        result = await db.execute(select(OutlineNode).where(OutlineNode.parent_id == parent_id))
        children = list(result.scalars().all())
        descendants = list(children)
        for child in children:
            descendants.extend(await collect_descendants(child.id))
        return descendants

    all_nodes = [node] + await collect_descendants(node.id)
    for n in all_nodes:
        await db.delete(n)
    return ResponseModel(message=f"已删除 {len(all_nodes)} 个节点")


@router.post("/generate", response_model=ResponseModel)
async def generate_outline(
    project_id: str,
    body: OutlineGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """AI生成大纲（基于招标文档和项目概况）"""
    project = await _get_project(project_id, db)

    # 获取文档文本
    doc_result = await db.execute(
        select(Document).where(Document.project_id == project_id).order_by(Document.created_at.desc())
    )
    docs = doc_result.scalars().all()
    doc_text = "\n\n".join(d.raw_text or "" for d in docs)

    if not doc_text and not project.project_info:
        raise HTTPException(status_code=400, detail="请先导入招标文档或填写项目概况")

    # 获取评分点
    from app.db.models import ScoringCriteria
    scoring_result = await db.execute(
        select(ScoringCriteria).where(ScoringCriteria.project_id == project_id)
    )
    scorings = list(scoring_result.scalars().all())

    # 调用 AI 生成大纲
    from app.services.outline_service import OutlineService
    from app.core.ai_config import get_ai_config
    import json as _json
    ai_cfg = await get_ai_config(db)
    service = OutlineService(ai_config=ai_cfg)
    outline_nodes = await service.generate_outline(
        project_info=project.project_info or "",
        document_text=doc_text,
        scoring_criteria=[
            {"category": s.category, "item": s.item_name, "score": float(s.max_score or 0), "desc": s.description}
            for s in scorings
        ],
        additional_requirements=body.additional_requirements,
    )

    # 类型保护：确保是 list[dict]
    logger.info(f"AI outline type: {type(outline_nodes)}, len: {len(outline_nodes) if isinstance(outline_nodes, (list, str)) else 'N/A'}")
    if isinstance(outline_nodes, str):
        try:
            outline_nodes = _json.loads(outline_nodes)
        except _json.JSONDecodeError:
            logger.error(f"Failed to parse outline JSON: {outline_nodes[:200]}")
            raise HTTPException(status_code=500, detail="AI 返回格式异常，请重试")
    if not isinstance(outline_nodes, list):
        logger.error(f"Outline is not list: {type(outline_nodes)}")
        raise HTTPException(status_code=500, detail="AI 返回格式异常，请重试")
    # 确保每个元素都是 dict
    outline_nodes = [n for n in outline_nodes if isinstance(n, dict)]
    if not outline_nodes:
        raise HTTPException(status_code=500, detail="AI 未返回有效大纲，请重试")

    # 清除旧大纲节点
    old_nodes = await db.execute(
        select(OutlineNode).where(OutlineNode.project_id == project_id)
    )
    for old in old_nodes.scalars().all():
        await db.delete(old)
    await db.flush()

    # 递归保存新大纲（含父子关系）
    async def save_nodes(nodes: list[dict], parent_id: str | None = None, order: int = 0) -> int:
        for node_data in nodes:
            node = OutlineNode(
                project_id=project_id,
                parent_id=parent_id,
                level=node_data["level"],
                title=node_data["title"],
                sort_order=order,
                ai_suggested=True,
                status="draft",
            )
            db.add(node)
            await db.flush()

            children = node_data.get("children", [])
            if children:
                await save_nodes(children, node.id, 0)

            order += 1
        return order

    await save_nodes(outline_nodes)

    # 重新获取树的完整结果
    result = await db.execute(
        select(OutlineNode).where(OutlineNode.project_id == project_id).order_by(OutlineNode.sort_order)
    )
    nodes = list(result.scalars().all())
    tree = _build_outline_tree(nodes)
    return ResponseModel(data=tree)


@router.post("/chat", response_model=ResponseModel)
async def chat_outline(
    project_id: str,
    body: OutlineChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """与Agent对话调整大纲（重新生成 + 用户反馈）"""
    project = await _get_project(project_id, db)

    # 获取招文
    doc_result = await db.execute(
        select(Document).where(Document.project_id == project_id).order_by(Document.created_at.desc())
    )
    docs = doc_result.scalars().all()
    doc_text = "\n\n".join(d.raw_text or "" for d in docs)

    # 获取评分点
    from app.db.models import ScoringCriteria
    scoring_result = await db.execute(
        select(ScoringCriteria).where(ScoringCriteria.project_id == project_id)
    )
    scorings = list(scoring_result.scalars().all())

    # 基于用户反馈重新生成大纲
    from app.services.outline_service import OutlineService
    from app.core.ai_config import get_ai_config
    ai_cfg = await get_ai_config(db)
    service = OutlineService(ai_config=ai_cfg)
    import json as _json
    new_outline = await service.generate_outline(
        project_info=project.project_info or "",
        document_text=doc_text,
        scoring_criteria=[
            {"category": s.category, "item": s.item_name, "score": float(s.max_score or 0), "desc": s.description}
            for s in scorings
        ],
        additional_requirements=body.message,
    )

    # 类型保护
    if isinstance(new_outline, str):
        try:
            new_outline = _json.loads(new_outline)
        except _json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="AI 返回格式异常，请重试")
    if not isinstance(new_outline, list):
        raise HTTPException(status_code=500, detail="AI 返回格式异常，请重试")

    # 保存新大纲（先清旧）
    old_nodes = await db.execute(select(OutlineNode).where(OutlineNode.project_id == project_id))
    for n in old_nodes.scalars().all():
        await db.delete(n)
    await db.flush()

    async def save_nodes(nodes: list[dict], parent_id: str | None = None, order: int = 0) -> int:
        for node_data in nodes:
            node = OutlineNode(
                project_id=project_id,
                parent_id=parent_id,
                level=node_data["level"],
                title=node_data["title"],
                sort_order=order,
                ai_suggested=True,
                status="draft",
            )
            db.add(node)
            await db.flush()
            children = node_data.get("children", [])
            if children:
                await save_nodes(children, node.id, 0)
            order += 1
        return order

    await save_nodes(new_outline)

    # 返回新大纲
    result = await db.execute(
        select(OutlineNode).where(OutlineNode.project_id == project_id).order_by(OutlineNode.sort_order)
    )
    nodes = list(result.scalars().all())
    tree = _build_outline_tree(nodes)

    return ResponseModel(data={
        "message": f"已根据「{body.message}」重新生成大纲",
        "outline": tree,
        "changes": ["大纲已重新生成"],
    })
