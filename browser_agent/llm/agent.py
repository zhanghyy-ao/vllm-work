from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Dict, List

from browser_agent.llm.client import LLMClient, compact_evidence
from browser_agent.strategy.research_patterns import default_decision_criteria, default_search_plan
from browser_agent.types import WorkflowNode, WorkflowSpec


def enhance_workflow_with_llm(workflow: WorkflowSpec, client: LLMClient | None) -> Dict[str, Any]:
    if client is None or not client.enabled:
        return {"used": False, "reason": "llm_disabled_or_api_key_missing"}
    system = (
        "You are a careful browser research planning agent. Return strict JSON only. "
        "Do not reveal hidden chain-of-thought. Instead provide a concise, auditable reasoning_outline. "
        "For comparison or recommendation tasks, decompose the work into product/category dimensions, "
        "subquestions, evidence needs, and multiple targeted web search queries. "
        "Prefer queries that gather independent evidence instead of one generic search. "
        "Do not include explanations outside JSON."
    )
    user = json.dumps(
        {
            "goal": workflow.goal,
            "domain": workflow.domain,
            "current_nodes": [node.to_dict() for node in workflow.nodes],
            "required_json_schema": {
                "task_type": "lookup|comparison|recommendation|research",
                "reasoning_outline": [
                    "brief visible planning point, not hidden chain-of-thought"
                ],
                "decision_criteria": [
                    {
                        "name": "criterion name",
                        "why_it_matters": "short reason",
                        "evidence_to_collect": "what to look for",
                    }
                ],
                "subquestions": ["specific research subquestion"],
                "search_plan": [
                    {
                        "query": "targeted search query",
                        "purpose": "what this search answers",
                        "source": "github|paper|shopping|video|general",
                    }
                ],
                "query": "best single fallback query",
                "rationale": "one sentence visible rationale",
            },
        },
        ensure_ascii=False,
    )
    result = client.chat_json(system, user)
    if not result.get("ok") or not (result.get("query") or result.get("search_plan")):
        return {"used": False, "reason": result.get("error", "missing_query")}
    search_plan = _normalize_search_plan(result, workflow)
    workflow.nodes[:] = _expand_nodes_from_search_plan(workflow, search_plan, result)
    workflow.summary = _summary_from_strategy(workflow, result, search_plan)
    workflow.confidence = min(0.9, max(workflow.confidence, 0.82 if len(search_plan) > 1 else 0.76))
    return {
        "used": True,
        "task_type": result.get("task_type", "research"),
        "query": search_plan[0]["query"] if search_plan else str(result.get("query", "")).strip(),
        "rationale": result.get("rationale", ""),
        "reasoning_outline": _string_list(result.get("reasoning_outline"), limit=6),
        "decision_criteria": _dict_list(result.get("decision_criteria"), limit=8),
        "subquestions": _string_list(result.get("subquestions"), limit=8),
        "search_plan": search_plan,
    }


def _guard_query(domain: str, goal: str, query: str) -> str:
    if domain == "shopping" and ("keyboard" in query.lower() or "键盘" in goal):
        return "学生 无线 机械键盘 推荐 价格"
    return query


def _normalize_search_plan(result: Dict[str, Any], workflow: WorkflowSpec) -> List[Dict[str, str]]:
    raw_plan = result.get("search_plan")
    items: List[Dict[str, str]] = []
    if isinstance(raw_plan, list):
        for item in raw_plan:
            if not isinstance(item, dict):
                continue
            query = str(item.get("query", "")).strip()
            if not query:
                continue
            source = str(item.get("source") or workflow.domain or "general").strip()
            if source not in {"github", "paper", "shopping", "video", "general"}:
                source = workflow.domain if workflow.domain in {"github", "paper", "shopping", "video"} else "general"
            items.append(
                {
                    "query": _guard_query(workflow.domain, workflow.goal, query),
                    "purpose": str(item.get("purpose") or "collect evidence").strip(),
                    "source": source,
                }
            )
    if not items:
        fallback_plan = default_search_plan(workflow.domain, workflow.goal)
        for item in fallback_plan:
            items.append(
                {
                    "query": _guard_query(workflow.domain, workflow.goal, str(item["query"]).strip()),
                    "purpose": str(item.get("purpose") or result.get("rationale") or "fallback search"),
                    "source": str(item.get("source") or workflow.domain),
                }
            )
    return _dedupe_search_plan(items, limit=_search_plan_limit(workflow.domain, result.get("task_type", "")))


def _search_plan_limit(domain: str, task_type: Any) -> int:
    text = str(task_type).lower()
    if domain == "shopping" or text in {"comparison", "recommendation"}:
        return 3
    if domain in {"github", "paper"}:
        return 3
    return 3


def _dedupe_search_plan(items: List[Dict[str, str]], limit: int) -> List[Dict[str, str]]:
    seen = set()
    deduped: List[Dict[str, str]] = []
    for item in items:
        key = (item["query"].lower(), item["source"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def _expand_nodes_from_search_plan(
    workflow: WorkflowSpec,
    search_plan: List[Dict[str, str]],
    strategy: Dict[str, Any],
) -> List[WorkflowNode]:
    first_url = ""
    for node in workflow.nodes:
        if node.action == "goto":
            first_url = str(node.inputs.get("url", ""))
            break
    nodes: List[WorkflowNode] = [
        WorkflowNode(
            id="n1",
            type="browser_task",
            instruction=_entry_instruction(workflow.domain),
            action="goto",
            inputs={"url": first_url or _default_url(workflow.domain)},
            depends_on=[],
            success_criteria=["action_ok", "evidence_or_fields"],
        )
    ]
    previous_id = "n1"
    next_idx = 2
    criteria = _dict_list(strategy.get("decision_criteria"), limit=8) or default_decision_criteria(workflow.domain, workflow.goal)
    subquestions = _string_list(strategy.get("subquestions"), limit=8)
    for item in search_plan:
        search_id = f"n{next_idx}"
        nodes.append(
            WorkflowNode(
                id=search_id,
                type="browser_task",
                instruction=f"围绕子问题检索资料：{item['purpose']}",
                action="search_web",
                inputs={
                    "query": item["query"],
                    "source": item["source"],
                    "llm_purpose": item["purpose"],
                    "decision_criteria": criteria,
                    "subquestions": subquestions,
                },
                depends_on=[previous_id],
                success_criteria=["action_ok", "evidence_or_fields"],
            )
        )
        collect_id = f"n{next_idx + 1}"
        nodes.append(
            WorkflowNode(
                id=collect_id,
                type="extract",
                instruction=f"抽取与本子问题相关的候选和证据：{item['purpose']}",
                action="collect_links",
                inputs={
                    "source": item["source"],
                    "query": item["query"],
                    "llm_purpose": item["purpose"],
                    "decision_criteria": criteria,
                },
                depends_on=[search_id],
                success_criteria=["action_ok", "evidence_or_fields"],
            )
        )
        previous_id = collect_id
        next_idx += 2
    if workflow.domain == "video":
        open_id = f"n{next_idx}"
        nodes.append(
            WorkflowNode(
                id=open_id,
                type="browser_task",
                instruction="打开最相关的视频候选页面，以便读取真实视频页内容",
                action="open_candidate",
                inputs={"source": workflow.domain, "rank": 0},
                depends_on=[previous_id],
                success_criteria=["action_ok", "evidence_or_fields"],
            )
        )
        previous_id = open_id
        next_idx += 1
    elif workflow.domain in {"github", "paper", "shopping", "general"}:
        deep_id = f"n{next_idx}"
        nodes.append(
            WorkflowNode(
                id=deep_id,
                type="extract",
                instruction="打开 Top 候选页面并进行深读，以支持更可靠的推荐和比较",
                action="deep_read_candidates",
                inputs={"source": workflow.domain, "limit": 3, "decision_criteria": criteria},
                depends_on=[previous_id],
                success_criteria=["action_ok", "evidence_or_fields"],
            )
        )
        previous_id = deep_id
        next_idx += 1

    nodes.append(
        WorkflowNode(
            id=f"n{next_idx}",
            type="artifact",
            instruction="读取当前视频/视频搜索页的元数据、简介和可见文本" if workflow.domain == "video" else "综合所有子问题证据，生成多维比较和推荐结论",
            action="extract_video" if workflow.domain == "video" else "summarize_text",
            inputs={
                "source": workflow.domain,
                "reasoning_outline": _string_list(strategy.get("reasoning_outline"), limit=6),
                "decision_criteria": criteria,
                "subquestions": subquestions,
            },
            depends_on=[previous_id],
            success_criteria=["action_ok", "evidence_or_fields"],
        )
    )
    if workflow.domain == "video":
        nodes.append(
            WorkflowNode(
                id=f"n{next_idx + 1}",
                type="artifact",
                instruction="综合视频候选、简介、可见字幕/章节和多模态预留信息，生成视频内容整理",
                action="summarize_text",
                inputs={
                    "source": workflow.domain,
                    "reasoning_outline": _string_list(strategy.get("reasoning_outline"), limit=6),
                    "decision_criteria": criteria,
                    "subquestions": subquestions,
                },
                depends_on=[f"n{next_idx}"],
                success_criteria=["action_ok", "evidence_or_fields"],
            )
        )
    return nodes


def _entry_instruction(domain: str) -> str:
    return {
        "github": "打开 GitHub 作为项目发现入口",
        "paper": "打开论文检索入口",
        "shopping": "打开搜索入口，准备进行多维商品调研",
        "video": "打开视频搜索入口",
    }.get(domain, "打开起始页面，准备进行多步资料调研")


def _default_url(domain: str) -> str:
    return {
        "github": "https://github.com",
        "paper": "https://arxiv.org",
        "shopping": "https://www.bing.com",
        "video": "https://www.bing.com",
    }.get(domain, "https://www.bing.com")


def _summary_from_strategy(workflow: WorkflowSpec, strategy: Dict[str, Any], search_plan: List[Dict[str, str]]) -> str:
    task_type = str(strategy.get("task_type") or "research")
    criteria = _dict_list(strategy.get("decision_criteria"), limit=4)
    criteria_names = [str(item.get("name", "")).strip() for item in criteria if item.get("name")]
    criteria_text = "、".join(criteria_names) if criteria_names else "多个证据维度"
    return f"{workflow.domain} {task_type} workflow for: {workflow.goal}. 将围绕 {criteria_text} 执行 {len(search_plan)} 组定向检索。"


def _string_list(value: Any, limit: int) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:limit]


def _dict_list(value: Any, limit: int) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)][:limit]


def build_llm_report(workflow: WorkflowSpec, memory_dump: Dict[str, Any], client: LLMClient | None) -> Dict[str, Any]:
    if client is None or not client.enabled:
        return {"used": False, "reason": "llm_disabled_or_api_key_missing"}
    evidence = compact_evidence(memory_dump.get("evidence", []))
    strategy = _workflow_strategy(workflow)
    system = (
        "You are a browser research report agent. Return strict JSON only. "
        "Ground every recommendation in the provided evidence. If evidence is weak, say so. "
        "Do not reveal hidden chain-of-thought; provide concise visible reasoning and comparison criteria only."
    )
    user = json.dumps(
        {
            "goal": workflow.goal,
            "domain": workflow.domain,
            "research_strategy": strategy,
            "evidence": evidence,
            "required_json_schema": {
                "summary": "Chinese summary",
                "reasoning_outline": ["concise visible reasoning step, not hidden chain-of-thought"],
                "subquestions": ["research subquestion answered by the evidence"],
                "search_plan": [
                    {"query": "query used or recommended", "purpose": "evidence purpose", "source": "source type"}
                ],
                "source_readings": [
                    {"name": "candidate/page name", "url": "source url", "useful_evidence": "Chinese evidence"}
                ],
                "recommendations": [{"name": "candidate", "url": "source url", "reason": "Chinese reason"}],
                "decision_criteria": [
                    {"name": "criterion", "finding": "Chinese finding", "importance": "high|medium|low"}
                ],
                "comparison_matrix": [
                    {
                        "name": "candidate",
                        "url": "source url",
                        "strengths": ["Chinese strength"],
                        "weaknesses": ["Chinese weakness or uncertainty"],
                        "best_for": "Chinese use case",
                    }
                ],
                "video_digest": {
                    "title": "video/page title",
                    "main_points": ["Chinese key point"],
                    "chapters_or_segments": ["known chapter/segment if available"],
                    "visual_follow_up": "what Gemini/key-frame analysis should inspect next",
                },
                "multimodal_notes": [
                    {"provider": "gemini", "purpose": "Chinese purpose", "status": "planned|available|not_needed"}
                ],
                "uncertainties": ["Chinese uncertainty"],
                "next_actions": ["Chinese next action"],
            },
        },
        ensure_ascii=False,
    )
    result = client.chat_json(system, user, temperature=0.2)
    if not result.get("ok"):
        retry_user = json.dumps(
            {
                "goal": workflow.goal,
                "domain": workflow.domain,
                "research_strategy": strategy,
                "evidence": evidence[:8],
                "instruction": "Return only valid minified JSON with keys: summary, reasoning_outline, subquestions, search_plan, source_readings, recommendations, decision_criteria, comparison_matrix, video_digest, multimodal_notes, uncertainties, next_actions.",
            },
            ensure_ascii=False,
        )
        result = client.chat_json(system, retry_user, temperature=0.0)
    if not result.get("ok"):
        return {"used": False, "reason": result.get("error", "llm_report_failed")}
    return {"used": True, "report": result}


def _workflow_strategy(workflow: WorkflowSpec) -> Dict[str, Any]:
    search_plan = []
    decision_criteria: List[Dict[str, Any]] = []
    subquestions: List[str] = []
    reasoning_outline: List[str] = []
    for node in workflow.nodes:
        if node.action == "search_web":
            search_plan.append(
                {
                    "query": node.inputs.get("query"),
                    "purpose": node.inputs.get("llm_purpose"),
                    "source": node.inputs.get("source"),
                }
            )
        if not decision_criteria and isinstance(node.inputs.get("decision_criteria"), list):
            decision_criteria = [item for item in node.inputs["decision_criteria"] if isinstance(item, dict)]
        if not subquestions and isinstance(node.inputs.get("subquestions"), list):
            subquestions = [str(item) for item in node.inputs["subquestions"]]
        if not reasoning_outline and isinstance(node.inputs.get("reasoning_outline"), list):
            reasoning_outline = [str(item) for item in node.inputs["reasoning_outline"]]
    return {
        "reasoning_outline": reasoning_outline[:6],
        "decision_criteria": decision_criteria[:8],
        "subquestions": subquestions[:8],
        "search_plan": search_plan[:6],
    }
