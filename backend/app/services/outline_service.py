"""大纲服务 - AI大纲生成和对话调整"""

import json
import re
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.ai_config import get_ai_config


def _extract_json(text: str) -> dict:
    """从 AI 回复中鲁棒地提取 JSON（处理 markdown 代码块和前后文字）"""
    # 尝试从 ```json ... ``` 中提取
    if "```json" in text:
        # 取最后一个 ```json 块（防止 AI 在示例中用了别的代码块）
        parts = text.rsplit("```json", 1)
        if len(parts) > 1:
            inner = parts[1].split("```", 1)[0].strip()
            return json.loads(inner)

    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("{") and part.endswith("}"):
                try:
                    return json.loads(part)
                except json.JSONDecodeError:
                    continue

    # 尝试用正则找到最大的 JSON 对象
    matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    for m in sorted(matches, key=len, reverse=True):
        try:
            return json.loads(m)
        except json.JSONDecodeError:
            continue

    raise ValueError("无法从回复中提取 JSON")

from app.prompts.outline_prompts import (
    OUTLINE_GENERATE_PROMPT,
    OUTLINE_CHAT_PROMPT,
    SCORING_EXTRACT_PROMPT,
)


class OutlineService:
    """大纲服务"""

    def __init__(self, ai_config: dict | None = None):
        cfg = ai_config or {}
        self.llm = ChatOpenAI(
            model=cfg.get("model", settings.AI_MODEL),
            temperature=cfg.get("temperature", settings.AI_TEMPERATURE),
            api_key=cfg.get("api_key", settings.OPENAI_API_KEY),
            base_url=cfg.get("base_url", settings.OPENAI_BASE_URL),
        )

    async def generate_outline(
        self,
        project_info: str,
        document_text: str,
        scoring_criteria: list[dict[str, Any]],
        additional_requirements: str | None = None,
    ) -> list[dict[str, Any]]:
        """基于招文和项目信息生成大纲

        Args:
            project_info: 项目概况
            document_text: 招标文档文本
            scoring_criteria: 评分标准列表
            additional_requirements: 用户额外要求

        Returns:
            大纲节点列表
        """
        # 格式化评分标准
        scoring_text = "\n".join(
            f"- {s.get('category', '')} | {s.get('item', '')} | {s.get('score', 0)}分 | {s.get('desc', '')}"
            for s in scoring_criteria
        ) if scoring_criteria else "（无明确评分标准，请按常规施工技术标大纲生成）"

        prompt = OUTLINE_GENERATE_PROMPT.format(
            project_info=project_info or "详见招标文档",
            document_text=document_text[:8000],  # 限制长度
            scoring_criteria=scoring_text,
            additional_requirements=additional_requirements or "无特殊要求",
        )

        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="请生成技术标大纲结构。"),
        ])

        # 解析JSON输出
        raw = response.content
        try:
            return _extract_json(raw)
        except (json.JSONDecodeError, ValueError):
            return self._fallback_outline_generation(document_text, project_info)

    async def chat_refine_outline(
        self,
        current_outline: list[dict[str, Any]],
        user_message: str,
        project_info: str,
    ) -> dict[str, Any]:
        """对话调整大纲

        Args:
            current_outline: 当前大纲树
            user_message: 用户的修改意见
            project_info: 项目概况

        Returns:
            包含消息和修改后大纲的字典
        """
        outline_text = json.dumps(current_outline, ensure_ascii=False, indent=2)

        prompt = OUTLINE_CHAT_PROMPT.format(
            project_info=project_info,
            current_outline=outline_text,
            user_message=user_message,
        )

        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=user_message),
        ])

        raw = response.content
        try:
            # 从 AI 回复中提取 JSON（AI 可能在 JSON 前后加文字）
            data = _extract_json(raw)
            return {
                "message": data.get("reply", "大纲已更新"),
                "outline": data.get("outline", current_outline),
                "changes": data.get("changes", []),
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "message": response.content,
                "outline": current_outline,
                "changes": [],
            }

    async def extract_scoring_criteria(
        self,
        document_text: str,
    ) -> list[dict[str, Any]]:
        """从招标文档中提取评分标准

        Args:
            document_text: 招标文档文本

        Returns:
            评分标准列表
        """
        prompt = SCORING_EXTRACT_PROMPT.format(
            document_text=document_text[:10000],
        )

        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="请提取评分标准。"),
        ])

        raw = response.content
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def _fallback_outline_generation(
        self,
        document_text: str,
        project_info: str,
    ) -> list[dict[str, Any]]:
        """大纲生成降级方案（AI不可用时的规则生成）"""
        # 尝试从文本中提取标题结构
        lines = document_text.split("\n")
        outline = []
        order = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 匹配数字章节格式
            import re
            m = re.match(r"^((?:\d+\.?)+)\s*(.+)$", line)
            if m:
                num_part = m.group(1)
                title = m.group(2)[:200]
                level = min(num_part.count(".") + 1, 4)
                outline.append({
                    "level": level,
                    "title": title,
                    "sort_order": order,
                })
                order += 1

        if not outline:
            outline.append({"level": 1, "title": project_info or "施工方案", "sort_order": 0})

        return outline
