"""内容生成 API"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db
from app.schemas import ResponseModel, SectionContentResponse
from app.db.models import Project, OutlineNode, SectionContent, ScoringCriteria

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["内容生成"])


async def _get_project(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.post("/sections/{outline_id}/generate")
async def generate_section(
    project_id: str,
    outline_id: str,
    db: AsyncSession = Depends(get_db),
):
    """生成单个章节内容（异步任务）"""
    project = await _get_project(project_id, db)

    # 获取大纲节点
    node_result = await db.execute(
        select(OutlineNode).where(OutlineNode.id == outline_id, OutlineNode.project_id == project_id)
    )
    node = node_result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="大纲节点不存在")

    # 获取评分点
    scoring_result = await db.execute(
        select(ScoringCriteria).where(ScoringCriteria.project_id == project_id)
    )
    scorings = list(scoring_result.scalars().all())

    # 获取兄弟节点（同级章节）
    siblings_result = await db.execute(
        select(OutlineNode).where(
            OutlineNode.project_id == project_id,
            OutlineNode.level == node.level,
        )
    )
    siblings = list(siblings_result.scalars().all())

    # 调用写作Agent生成内容
    from app.services.generate_service import GenerateService
    service = GenerateService()

    content_text = await service.generate_section(
        section_title=node.title,
        section_level=node.level,
        project_info=project.project_info or "",
        scoring_criteria=[
            {"category": s.category, "item": s.item_name, "score": float(s.max_score or 0), "desc": s.description}
            for s in scorings
        ],
        sibling_sections=[s.title for s in siblings if s.id != node.id],
    )

    # 保存生成内容（覆盖之前的版本）
    existing = await db.execute(
        select(SectionContent).where(SectionContent.outline_id == outline_id)
    )
    section = existing.scalar_one_or_none()

    if section:
        section.content = content_text
        section.word_count = len(content_text)
        section.version += 1
        section.status = "generated"
    else:
        section = SectionContent(
            project_id=project_id,
            outline_id=outline_id,
            content=content_text,
            word_count=len(content_text),
            version=1,
        )
        db.add(section)

    # 更新大纲节点状态
    node.status = "confirmed"
    await db.flush()

    return ResponseModel(data={
        "id": str(section.id),
        "outline_id": outline_id,
        "content": content_text,
        "word_count": len(content_text),
        "version": section.version,
    })


@router.get("/sections/{outline_id}/stream")
async def generate_section_stream(
    project_id: str,
    outline_id: str,
    db: AsyncSession = Depends(get_db),
):
    """流式生成章节内容（SSE）"""
    project = await _get_project(project_id, db)

    node_result = await db.execute(
        select(OutlineNode).where(OutlineNode.id == outline_id, OutlineNode.project_id == project_id)
    )
    node = node_result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="大纲节点不存在")

    from app.services.generate_service import GenerateService
    service = GenerateService()

    async def event_stream():
        yield f"data: {json.dumps({'type': 'start', 'outline_id': outline_id, 'title': node.title})}\n\n"

        full_content = ""
        async for chunk in service.generate_section_stream(
            section_title=node.title,
            section_level=node.level,
            project_info=project.project_info or "",
        ):
            full_content += chunk
            yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'word_count': len(full_content)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/generate-all")
async def generate_all_sections(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """一键生成所有章节内容（异步启动后台任务）"""
    await _get_project(project_id, db)

    # 获取所有大纲节点
    result = await db.execute(
        select(OutlineNode).where(OutlineNode.project_id == project_id).order_by(OutlineNode.sort_order)
    )
    nodes = list(result.scalars().all())

    if not nodes:
        raise HTTPException(status_code=400, detail="暂无大纲，请先生成大纲")

    return ResponseModel(data={
        "total_sections": len(nodes),
        "message": "已启动批量生成任务，请通过 SSE 监听进度",
    })


@router.get("/compose", response_model=ResponseModel)
async def compose_draft(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """组装初稿"""
    await _get_project(project_id, db)

    # 获取大纲和内容
    result = await db.execute(
        select(OutlineNode).where(OutlineNode.project_id == project_id).order_by(OutlineNode.sort_order)
    )
    nodes = list(result.scalars().all())

    # 获取所有内容
    outline_ids = [n.id for n in nodes]
    content_result = await db.execute(
        select(SectionContent).where(SectionContent.outline_id.in_(outline_ids))
    )
    contents = {str(c.outline_id): c for c in content_result.scalars().all()}

    # 组装
    from app.services.generate_service import GenerateService
    service = GenerateService()
    draft = service.compose_draft(nodes, contents)

    return ResponseModel(data={
        "draft": draft,
        "word_count": len(draft),
        "section_count": len([c for c in contents.values() if c.content]),
    })
