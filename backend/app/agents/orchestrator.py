"""编标总调度器 - 基于 LangGraph 状态机

负责协调整个编标流程：
1. 文档解析 → 2. 评分提取 → 3. 大纲生成 → 4. 子节生成 → 5. 组装 → 6. 审查
"""

from typing import TypedDict, Annotated, Any
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings


class BidState(TypedDict):
    """编标流程状态"""
    # 输入
    project_id: str
    document_texts: list[str]          # 招文文本列表
    project_info: str                  # 项目概况

    # 中间产物
    scoring_criteria: list[dict[str, Any]]  # 评分点
    outline: list[dict[str, Any]]           # 大纲（树形JSON）
    outline_status: str                     # draft / confirmed / locked

    # 生成结果
    sections_content: dict[str, dict[str, Any]]  # {outline_id: {title, content, status}}

    # 审查
    review_results: list[dict[str, Any]]
    review_status: str                       # pending / passed / needs_revision

    # 流程控制
    current_step: str                        # 当前步骤
    needs_user_input: bool                   # 是否需要用户干预
    user_feedback: str                       # 用户反馈
    messages: Annotated[list[str], operator.add]  # 消息历史


class BidOrchestrator:
    """编标总调度器"""

    STEPS = [
        "parse_document",
        "extract_scoring",
        "generate_outline",
        "wait_outline_confirm",
        "assign_generation",
        "generate_content",
        "compose_draft",
        "review_draft",
    ]

    def __init__(self):
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建编标流程状态图"""
        workflow = StateGraph(BidState)

        # ── 节点注册 ──
        workflow.add_node("parse_document", self._parse_document)
        workflow.add_node("extract_scoring", self._extract_scoring)
        workflow.add_node("generate_outline", self._generate_outline)
        workflow.add_node("wait_outline_confirm", self._wait_outline_confirm)
        workflow.add_node("refine_outline", self._refine_outline)
        workflow.add_node("assign_generation", self._assign_generation)
        workflow.add_node("generate_content", self._generate_content)
        workflow.add_node("compose_draft", self._compose_draft)
        workflow.add_node("review_draft", self._review_draft)

        # ── 流程定义 ──
        workflow.set_entry_point("parse_document")
        workflow.add_edge("parse_document", "extract_scoring")
        workflow.add_edge("extract_scoring", "generate_outline")

        # 分支：大纲生成后等待确认或修改
        workflow.add_conditional_edges(
            "generate_outline",
            self._should_wait_for_outline,
            {
                "wait": "wait_outline_confirm",
                "confirmed": "assign_generation",
            }
        )

        workflow.add_edge("refine_outline", "generate_outline")
        workflow.add_edge("wait_outline_confirm", END)
        workflow.add_edge("assign_generation", "generate_content")
        workflow.add_edge("generate_content", "compose_draft")
        workflow.add_edge("compose_draft", "review_draft")

        # 审查后分支
        workflow.add_conditional_edges(
            "review_draft",
            self._should_revise,
            {
                "pass": END,
                "revise": "generate_content",
            }
        )

        return workflow.compile(checkpointer=self.checkpointer)

    # ═══════════════════════════════════
    # 节点实现
    # ═══════════════════════════════════

    async def _parse_document(self, state: BidState) -> BidState:
        """节点1：文档解析（已在导入时完成，此处做归一化）"""
        state["current_step"] = "parse_document"
        state["messages"].append("文档解析完成")

        if not state.get("document_texts"):
            state["document_texts"] = []

        return state

    async def _extract_scoring(self, state: BidState) -> BidState:
        """节点2：提取评分标准"""
        state["current_step"] = "extract_scoring"

        from app.services.outline_service import OutlineService
        service = OutlineService()

        all_text = "\n\n".join(state.get("document_texts", []))
        if all_text:
            scoring = await service.extract_scoring_criteria(all_text)
            state["scoring_criteria"] = scoring
            state["messages"].append(f"提取到 {len(scoring)} 个评分标准")
        else:
            state["scoring_criteria"] = []
            state["messages"].append("未找到文档文本，跳过评分提取")

        return state

    async def _generate_outline(self, state: BidState) -> BidState:
        """节点3：AI生成大纲"""
        state["current_step"] = "generate_outline"

        from app.services.outline_service import OutlineService
        service = OutlineService()

        all_text = "\n\n".join(state.get("document_texts", []))
        outline = await service.generate_outline(
            project_info=state.get("project_info", ""),
            document_text=all_text,
            scoring_criteria=state.get("scoring_criteria", []),
        )

        state["outline"] = outline
        state["outline_status"] = "draft"
        state["messages"].append(f"生成大纲：{len(outline)} 个一级章节")

        return state

    async def _wait_outline_confirm(self, state: BidState) -> BidState:
        """节点4：等待用户确认大纲"""
        state["current_step"] = "wait_outline_confirm"
        state["needs_user_input"] = True

        if state.get("user_feedback"):
            state["outline_status"] = "confirmed"
            state["needs_user_input"] = False
        else:
            state["outline_status"] = "draft"

        return state

    async def _refine_outline(self, state: BidState) -> BidState:
        """节点4a：调整大纲"""
        state["current_step"] = "refine_outline"

        from app.services.outline_service import OutlineService
        service = OutlineService()

        result = await service.chat_refine_outline(
            current_outline=state.get("outline", []),
            user_message=state.get("user_feedback", ""),
            project_info=state.get("project_info", ""),
        )

        state["outline"] = result.get("outline", state["outline"])
        state["messages"].append(f"大纲调整：{result.get('message', '已更新')}")
        state["user_feedback"] = ""

        return state

    async def _assign_generation(self, state: BidState) -> BidState:
        """节点5：分配生成任务"""
        state["current_step"] = "assign_generation"
        state["sections_content"] = {}
        state["messages"].append("已分配章节生成任务")
        return state

    async def _generate_content(self, state: BidState) -> BidState:
        """节点6：生成各章节内容"""
        state["current_step"] = "generate_content"

        from app.services.generate_service import GenerateService
        service = GenerateService()

        outline = state.get("outline", [])

        async def process_node(node: dict[str, Any]) -> None:
            """递归处理大纲节点生成内容"""
            content = await service.generate_section(
                section_title=node["title"],
                section_level=node.get("level", 1),
                project_info=state.get("project_info", ""),
                scoring_criteria=state.get("scoring_criteria", []),
                sibling_sections=[
                    c["title"] for c in outline
                    if c.get("level") == node.get("level") and c["title"] != node["title"]
                ],
            )
            state["sections_content"][node["title"]] = {
                "title": node["title"],
                "level": node.get("level", 1),
                "content": content,
                "status": "generated",
            }
            for child in node.get("children", []):
                await process_node(child)

        # 按顺序处理所有一级节点
        for section in outline:
            await process_node(section)

        state["messages"].append(f"已生成 {len(state['sections_content'])} 个章节内容")
        return state

    async def _compose_draft(self, state: BidState) -> BidState:
        """节点7：组装初稿"""
        state["current_step"] = "compose_draft"

        from app.services.generate_service import GenerateService
        service = GenerateService()

        # 递归收集大纲内容
        def collect_sections(nodes: list[dict], level: int = 1) -> str:
            parts = []
            for node in nodes:
                title = node["title"]
                marker = "#" * min(level, 6)
                parts.append(f"\n{marker} {title}\n")

                sec = state["sections_content"].get(title, {})
                if sec.get("content"):
                    parts.append(sec["content"])
                    parts.append("")

                children = node.get("children", [])
                if children:
                    parts.append(collect_sections(children, level + 1))
            return "\n".join(parts)

        draft = collect_sections(state.get("outline", []))
        state["messages"].append(f"初稿组装完成：{len(draft)} 字")
        return state

    async def _review_draft(self, state: BidState) -> BidState:
        """节点8：AI审查"""
        state["current_step"] = "review_draft"
        state["review_status"] = "pending"

        # 从 sections_content 获取所有已生成内容
        all_content = "\n\n".join(
            f"## {k}\n{v.get('content', '')}"
            for k, v in state.get("sections_content", {}).items()
        )

        from app.services.generate_service import GenerateService
        service = GenerateService()
        llm = service.llm

        from app.prompts.generate_prompts import REVIEW_PROMPT
        from langchain_core.messages import HumanMessage, SystemMessage

        prompt = REVIEW_PROMPT.format(
            project_info=state.get("project_info", ""),
            scoring_criteria=state.get("scoring_criteria", []),
            draft_text=all_content[:15000],
        )

        response = await llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="请审查以上技术标内容。"),
        ])

        import json
        raw = response.content
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            review_result = json.loads(raw)
        except json.JSONDecodeError:
            review_result = {"overall_score": 70, "issues": [], "summary": raw}

        state["review_results"] = [review_result]
        state["review_status"] = "completed"
        state["messages"].append(f"审查完成：评分 {review_result.get('overall_score', 'N/A')}")
        return state

    # ═══════════════════════════════════
    # 条件分支
    # ═══════════════════════════════════

    def _should_wait_for_outline(self, state: BidState) -> str:
        """判断是否需要等待用户确认大纲"""
        if state.get("user_feedback"):
            return "confirmed"  # 已确认
        return "wait"  # 等待确认

    def _should_revise(self, state: BidState) -> str:
        """判断审查是否通过"""
        review = state.get("review_results", [{}])[0] if state.get("review_results") else {}
        score = review.get("overall_score", 0)
        issues = review.get("issues", [])

        # 有高严重问题或总分低于70则需要修改
        high_issues = [i for i in issues if i.get("severity") == "high"]
        if high_issues or score < 70:
            return "revise"
        return "pass"
