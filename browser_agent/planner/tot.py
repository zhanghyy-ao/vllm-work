from __future__ import annotations

import re
import uuid
from typing import List

from browser_agent.strategy.research_patterns import default_decision_criteria
from browser_agent.types import Observation, WorkflowNode, WorkflowSpec


def detect_domain(goal: str, requested_domain: str = "auto") -> str:
    if requested_domain != "auto":
        return requested_domain
    text = goal.lower()
    if any(token in text for token in ["github", "repo", "repository", "代码", "开源", "项目"]):
        return "github"
    if any(token in text for token in ["paper", "arxiv", "论文", "scholar", "文献"]):
        return "paper"
    if any(token in text for token in ["购物", "商品", "价格", "键盘", "耳机", "推荐买"]):
        return "shopping"
    if any(token in text for token in ["视频", "b站", "bilibili", "youtube", "字幕", "关键帧", "课程", "学习路线", "内容整理"]):
        return "video"
    return "general"


def _keywords(goal: str) -> str:
    cleaned = re.sub(r"[，。！？,.!?]", " ", goal).strip()
    replacements = {
        "帮我": " ",
        "找": " ",
        "相关": " ",
        "开源项目": " open source project ",
        "论文": " paper ",
        "最近": " recent ",
        "多模态": " multimodal ",
        "OOD": " out-of-distribution ",
        "代码": " code ",
    }
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)
    return " ".join(cleaned.split()) or goal


def _shopping_query(goal: str) -> str:
    if "耳机" in goal:
        budget = "1000元以内" if "1000" in goal else ""
        return " ".join(part for part in ["site:post.smzdm.com", budget, "头戴式 降噪耳机 推荐 评测 通勤 办公"] if part).strip()
    return _keywords(goal)


def _shopping_followup_query(goal: str) -> str:
    if "耳机" in goal:
        return "WH-CH720N W820NB Space Q45 降噪耳机 对比 评测 缺点"
    return _shopping_query(goal)


def _video_query(goal: str) -> str:
    if "clip" in goal.lower() or "CLIP" in goal:
        return "CLIP 多模态 模型 入门 教程 视频 讲解"
    return _keywords(goal)


def _github_query(goal: str) -> str:
    text = goal.lower()
    if any(token in text for token in ["浏览器", "browser", "自动化", "agent", "智能体"]):
        return "browser automation agent LLM"
    if "多模态" in goal or "multimodal" in text:
        return "multimodal OOD open source"
    return _keywords(goal)


def _shopping_strategy_inputs(goal: str) -> dict:
    return {
        "decision_criteria": default_decision_criteria("shopping", goal),
        "subquestions": [
            "预算内有哪些主流品牌和型号值得进入候选池？",
            "候选耳机分别属于什么类型，是否适合通勤和办公室？",
            "价格、音质、降噪、舒适度和用户评价分别有什么证据？",
            "每个候选有哪些差评、短板或购买风险？",
        ],
        "reasoning_outline": [
            "先按预算、品牌型号、类型场景、核心体验和风险点拆解任务。",
            "第一轮检索收集榜单/评测形成候选池，第二轮检索用具体型号做交叉对比。",
            "深读候选页面抽取价格、评价和缺点，再生成对比矩阵。",
        ],
    }


def _node(idx: int, node_type: str, instruction: str, action: str, **inputs) -> WorkflowNode:
    return WorkflowNode(
        id=f"n{idx}",
        type=node_type,
        instruction=instruction,
        action=action,
        inputs=inputs,
        depends_on=[f"n{idx - 1}"] if idx > 1 else [],
        success_criteria=["action_ok", "evidence_or_fields"],
    )


def _nodes_for(domain: str, goal: str, start_url: str) -> List[WorkflowNode]:
    if domain == "shopping":
        query = _shopping_query(goal)
    elif domain == "video":
        query = _video_query(goal)
    elif domain == "github":
        query = _github_query(goal)
    else:
        query = _keywords(goal)
    if domain == "github":
        return [
            _node(1, "browser_task", "打开 GitHub 作为项目发现入口", "goto", url=start_url or "https://github.com"),
            _node(2, "browser_task", "搜索相关开源仓库", "search_web", query=query, source="github"),
            _node(3, "extract", "抽取仓库候选链接与页面文本", "collect_links", source="github"),
            _node(4, "extract", "打开 Top 候选仓库并深读 README/页面信息", "deep_read_candidates", source="github", limit=3),
            _node(5, "artifact", "基于证据生成项目推荐摘要", "summarize_text", source="github"),
        ]
    if domain == "paper":
        return [
            _node(1, "browser_task", "打开论文检索入口", "goto", url=start_url or "https://arxiv.org"),
            _node(2, "browser_task", "搜索相关论文", "search_web", query=query, source="paper"),
            _node(3, "extract", "抽取论文候选链接与摘要片段", "collect_links", source="paper"),
            _node(4, "extract", "打开 Top 候选论文并深读摘要页", "deep_read_candidates", source="paper", limit=3),
            _node(5, "artifact", "生成论文调研摘要", "summarize_text", source="paper"),
        ]
    if domain == "shopping":
        strategy = _shopping_strategy_inputs(goal)
        return [
            _node(1, "browser_task", "打开通用搜索入口", "goto", url=start_url or "https://duckduckgo.com/html/"),
            _node(2, "browser_task", "搜索商品榜单与评价", "search_web", query=query, source="shopping", **strategy),
            _node(3, "extract", "抽取商品候选链接", "collect_links", source="shopping", query=query, **strategy),
            _node(4, "browser_task", "搜索具体型号对比与评测", "search_web", query=_shopping_followup_query(goal), source="shopping", **strategy),
            _node(5, "extract", "抽取具体型号候选链接", "collect_links", source="shopping", query=_shopping_followup_query(goal), **strategy),
            _node(6, "extract", "打开 Top 候选商品/评测页面并抽取价格与评价线索", "deep_read_candidates", source="shopping", limit=5, **strategy),
            _node(7, "artifact", "生成购买建议摘要", "summarize_text", source="shopping", **strategy),
        ]
    if domain == "video":
        return [
            _node(1, "browser_task", "打开视频搜索入口", "goto", url=start_url or "https://duckduckgo.com/html/"),
            _node(2, "browser_task", "搜索学习视频", "search_web", query=query, source="video"),
            _node(3, "extract", "抽取视频候选与描述", "collect_links", source="video"),
            _node(4, "browser_task", "打开最相关的视频候选页面", "open_candidate", source="video", rank=0),
            _node(5, "extract", "读取视频页的元数据、简介和可见文本", "extract_video", source="video"),
            _node(6, "artifact", "生成视频内容整理摘要", "summarize_text", source="video"),
        ]
    return [
        _node(1, "browser_task", "打开起始页面", "goto", url=start_url or "https://example.com"),
        _node(2, "browser_task", "搜索目标相关资料", "search_web", query=query, source="general"),
        _node(3, "extract", "抽取页面链接与正文", "collect_links", source="general"),
        _node(4, "artifact", "生成结构化摘要", "summarize_text", source="general"),
    ]


def plan_goal(goal: str, observation: Observation, domain: str = "auto") -> WorkflowSpec:
    """Build a deterministic workflow template for the platform MVP.

    This is deterministic by design for stable harness behavior.
    """
    resolved_domain = detect_domain(goal, domain)
    template = f"{resolved_domain}_research" if resolved_domain in {"github", "paper"} else f"{resolved_domain}_workflow"
    return WorkflowSpec(
        workflow_id=str(uuid.uuid4()),
        template=template,
        goal=goal.strip(),
        domain=resolved_domain,
        summary=f"{resolved_domain} workflow for: {goal.strip()}",
        nodes=_nodes_for(resolved_domain, goal, observation.url),
        confidence=0.78 if resolved_domain in {"github", "paper"} else 0.68,
        output_schema={
            "summary": "str",
            "candidates": "list",
            "recommendations": "list",
            "decision_criteria": "list",
            "comparison_matrix": "list",
            "video_digest": "dict",
            "multimodal_notes": "list",
            "uncertainties": "list",
            "next_actions": "list",
        },
    )
