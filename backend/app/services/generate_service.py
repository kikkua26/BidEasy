"""内容生成服务"""

import json
from typing import AsyncGenerator, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.services.outline_service import _get_content
from app.prompts.generate_prompts import SECTION_GENERATE_PROMPT
from app.db.models import OutlineNode, SectionContent


class GenerateService:
    """内容生成服务"""

    def __init__(self, ai_config: dict | None = None):
        cfg = ai_config or {}
        extra = cfg.get("extra_headers", {})
        kwargs: dict = {
            "model": cfg.get("model", settings.AI_MODEL),
            "temperature": cfg.get("temperature", settings.AI_TEMPERATURE),
            "base_url": cfg.get("base_url", settings.OPENAI_BASE_URL),
            "streaming": True,
        }
        if extra:
            kwargs["api_key"] = "not-used"
            kwargs["default_headers"] = extra
        else:
            kwargs["api_key"] = cfg.get("api_key", settings.OPENAI_API_KEY)
        self.llm = ChatOpenAI(**kwargs)

    async def generate_section(
        self,
        section_title: str,
        section_level: int,
        project_info: str,
        scoring_criteria: list[dict[str, Any]],
        sibling_sections: list[str],
        parent_title: str = "",
    ) -> str:
        """生成单个章节内容

        Args:
            section_title: 章节标题
            section_level: 章节层级
            project_info: 项目概况
            scoring_criteria: 评分标准
            sibling_sections: 同级章节列表

        Returns:
            生成的内容文本
        """
        scoring_text = "\n".join(
            f"- [{s.get('category', '')}] {s.get('item', '')}: {s.get('desc', '')} (满分{s.get('score', 0)}分)"
            for s in scoring_criteria
        ) if scoring_criteria else "无特定评分标准"

        prompt = SECTION_GENERATE_PROMPT.format(
            project_info=project_info,
            section_title=section_title,
            section_level=section_level,
            scoring_points=scoring_text,
            sibling_sections="\n".join(f"- {s}" for s in sibling_sections) if sibling_sections else "无",
        )

        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=f"请生成「{section_title}」的详细内容。"),
        ])

        return _get_content(response)

    async def generate_section_stream(
        self,
        section_title: str,
        section_level: int,
        project_info: str,
    ) -> AsyncGenerator[str, None]:
        """流式生成章节内容

        Args:
            section_title: 章节标题
            section_level: 章节层级
            project_info: 项目概况

        Yields:
            生成的文本片段
        """
        prompt = SECTION_GENERATE_PROMPT.format(
            project_info=project_info,
            section_title=section_title,
            section_level=section_level,
            scoring_points="按施工技术标规范要求",
            sibling_sections="无",
        )

        async for chunk in self.llm.astream([
            SystemMessage(content=prompt),
            HumanMessage(content=f"请生成「{section_title}」的详细内容。"),
        ]):
            # 推理模型内容在 reasoning_content
            text = chunk.content or ""
            if not text and hasattr(chunk, "additional_kwargs"):
                text = chunk.additional_kwargs.get("reasoning_content", "")
            if text:
                yield text

    def compose_draft(
        self,
        nodes: list[OutlineNode],
        contents: dict[str, SectionContent],
    ) -> str:
        """组装初稿

        Args:
            nodes: 大纲节点列表
            contents: 章节内容字典 {outline_id: SectionContent}

        Returns:
            完整的初稿文本
        """
        # 按 level 和 sort_order 排序
        sorted_nodes = sorted(nodes, key=lambda n: (n.sort_order, n.level))

        draft_parts = []
        prev_level = 0

        for node in sorted_nodes:
            # 添加章节标题
            indent = "#" * node.level
            draft_parts.append(f"\n{indent} {node.title}\n")

            # 添加内容
            content = contents.get(str(node.id))
            if content and content.content:
                draft_parts.append(content.content)
                draft_parts.append("")
            else:
                draft_parts.append("（内容待生成）\n")

            prev_level = node.level

        return "\n".join(draft_parts)
