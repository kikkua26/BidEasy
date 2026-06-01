"""项目 API 路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas import (
    ResponseModel,
    PaginatedResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)
from app.db.models import Project
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/projects", tags=["项目管理"])


@router.get("", response_model=PaginatedResponse)
async def list_projects(
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取项目列表"""
    query = select(Project)
    if status:
        query = query.where(Project.status == status)
    query = query.order_by(Project.updated_at.desc())

    total = (await db.execute(select(Project))).scalars().all()
    items = (await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return PaginatedResponse(
        data={
            "list": [ProjectResponse.model_validate(p) for p in items],
            "total": len(total),
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("", response_model=ResponseModel)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建项目"""
    project = Project(**body.model_dump())
    db.add(project)
    await db.flush()
    return ResponseModel(data=ProjectResponse.model_validate(project).model_dump())


@router.get("/{project_id}", response_model=ResponseModel)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取项目详情"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ResponseModel(data=ProjectResponse.model_validate(project))


@router.put("/{project_id}", response_model=ResponseModel)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新项目"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    await db.flush()
    return ResponseModel(data=ProjectResponse.model_validate(project))


@router.delete("/{project_id}", response_model=ResponseModel)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除项目"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    await db.delete(project)
    return ResponseModel(message="项目已删除")
