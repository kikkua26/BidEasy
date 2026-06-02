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
    """生成章节内容（支持递归生成子节）"""
    import json as _json
    from app.services.generate_service import GenerateService

    project = await _get_project(project_id, db)
    service = GenerateService()

    # 获取大纲树（用于递归生成）
    all_nodes_result = await db.execute(
        select(OutlineNode).where(OutlineNode.project_id == project_id)
    )
    all_nodes = {str(n.id): n for n in all_nodes_result.scalars().all()}
    from app.api.v1.outline import _build_outline_tree
    tree = _build_outline_tree(list(all_nodes.values()))

    # 找到目标节点
    def find_node(nodes: list, target_id: str):
        for n in nodes:
            if n["id"] == target_id:
                return n
            found = find_node(n.get("children", []), target_id)
            if found:
                return found
        return None

    target_node = find_node(tree, outline_id)
    if not target_node:
        raise HTTPException(status_code=404, detail="大纲节点不存在")

    # 获取评分点
    scoring_result = await db.execute(
        select(ScoringCriteria).where(ScoringCriteria.project_id == project_id)
    )
    scorings = list(scoring_result.scalars().all())
    scoring_list = [
        {"category": s.category, "item": s.item_name, "score": float(s.max_score or 0), "desc": s.description}
        for s in scorings
    ]

    # 收集所有要生成的节点（自身 + 所有子孙）
    def collect_flat(node: dict) -> list[dict]:
        result = [node]
        for child in node.get("children", []):
            result.extend(collect_flat(child))
        return result

    nodes_to_generate = collect_flat(target_node)
    children_contents: dict[str, dict] = {}
    all_generated_content = ""
    total_word_count = 0

    # 依次生成（可被前端 AbortController 中断）
    for i, nd in enumerate(nodes_to_generate):
        siblings = [
            c["title"] for c in target_node.get("children", [])
            if c["id"] != nd["id"]
        ]
        content_text = await service.generate_section(
            section_title=nd["title"],
            section_level=nd.get("level", 1),
            project_info=project.project_info or "",
            scoring_criteria=scoring_list,
            sibling_sections=siblings,
            parent_title=target_node["title"] if nd["id"] != target_node["id"] else "",
        )

        # 保存
        existing = await db.execute(
            select(SectionContent).where(SectionContent.outline_id == nd["id"])
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
                outline_id=nd["id"],
                content=content_text,
                word_count=len(content_text),
                version=1,
            )
            db.add(section)

        # 更新节点状态
        node_obj = all_nodes.get(nd["id"])
        if node_obj:
            node_obj.status = "confirmed"

        await db.flush()

        if nd["id"] != outline_id:
            children_contents[nd["id"]] = {
                "title": nd["title"],
                "content": content_text,
                "word_count": len(content_text),
            }
        total_word_count += len(content_text)

        if i == 0:
            all_generated_content = content_text

    return ResponseModel(data={
        "outline_id": outline_id,
        "content": all_generated_content,
        "word_count": total_word_count,
        "generated_count": len(nodes_to_generate),
        "children_contents": children_contents,
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
    from app.core.ai_config import get_ai_config
    ai_cfg = await get_ai_config(db)
    service = GenerateService(ai_config=ai_cfg)

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
    from app.core.ai_config import get_ai_config
    ai_cfg = await get_ai_config(db)
    service = GenerateService(ai_config=ai_cfg)
    draft = service.compose_draft(nodes, contents)

    return ResponseModel(data={
        "draft": draft,
        "word_count": len(draft),
        "section_count": len([c for c in contents.values() if c.content]),
    })
