from __future__ import annotations

from typing import Any, Dict, List

from browser_agent.agents.page_state import (
    first_searchbox_ref,
    has_candidate_links,
    has_deep_read_step,
    has_successful_deep_read,
    has_post_search_evidence_step,
    has_successful_collect_links,
    low_quality_current_page,
    looks_like_results_page,
    query_from_observation_url,
    repeated_search_like_behavior,
    supports_in_page_task_search,
)
from browser_agent.types import Observation, WorkflowNode


def prefer_in_page_react(
    node: WorkflowNode,
    observation: Observation,
    traces: List[Dict[str, Any]],
    step_id: int,
    source: str,
    target_stage: str,
    page_query: str,
) -> WorkflowNode | None:
    if node.action not in {"search_web", "wait", "goto"}:
        return None
    if has_candidate_links(observation) and not has_deep_read_step(traces) and not low_quality_current_page(observation, target_stage):
        return WorkflowNode(
            id=f"d{step_id}",
            type="agent_dynamic_guarded",
            instruction="当前页已有候选链接，先打开或深读候选，不再盲目发起新搜索。",
            action="deep_read_candidates" if has_successful_collect_links(traces) else "open_candidate",
            inputs={
                "source": source,
                "dynamic": True,
                "rank": 0,
                "limit": 3,
                "requirement_slot": target_stage or "candidate_pool",
                "evidence_stage": target_stage or "candidate_pool",
                "rationale": "ReAct guard: candidate links already exist on the current page.",
                "checklist_status": node.inputs.get("checklist_status", []),
                "planner_suggested_action": node.action,
                "planner_suggested_rationale": node.inputs.get("rationale", ""),
                "multimodal_planning_used": node.inputs.get("multimodal_planning_used", False),
            },
            depends_on=node.depends_on,
            success_criteria=["action_ok", "evidence_or_fields"],
        )
    search_box = first_searchbox_ref(observation)
    if (
        search_box is not None
        and page_query
        and supports_in_page_task_search(observation, source, page_query)
    ):
        return WorkflowNode(
            id=f"d{step_id}",
            type="agent_dynamic_guarded",
            instruction="当前页可直接通过搜索框推进任务，优先在页内输入并提交。",
            action="type_text",
            inputs={
                "source": source,
                "dynamic": True,
                "element_ref": search_box,
                "text": page_query,
                "clear": True,
                "submit_after_type": True,
                "requirement_slot": target_stage or "candidate_pool",
                "evidence_stage": target_stage or "candidate_pool",
                "rationale": "ReAct guard: visible search box found on the current page.",
                "checklist_status": node.inputs.get("checklist_status", []),
                "planner_suggested_action": node.action,
                "planner_suggested_rationale": node.inputs.get("rationale", ""),
                "multimodal_planning_used": node.inputs.get("multimodal_planning_used", False),
            },
            depends_on=node.depends_on,
            success_criteria=["action_ok", "evidence_or_fields"],
        )
    return None


def apply_repeat_breaker(
    node: WorkflowNode,
    observation: Observation,
    traces: List[Dict[str, Any]],
    step_id: int,
    source: str,
    target_stage: str,
) -> WorkflowNode | None:
    if node.action not in {"search_web", "type_text"}:
        return None
    if not repeated_search_like_behavior(node, traces):
        return None
    if has_successful_collect_links(traces) and has_candidate_links(observation) and not has_successful_deep_read(traces):
        return WorkflowNode(
            id=f"d{step_id}",
            type="agent_dynamic_guarded",
            instruction="相近检索已重复出现，直接进入候选页面深读。",
            action="deep_read_candidates",
            inputs={
                "source": source,
                "dynamic": True,
                "limit": 3,
                "requirement_slot": target_stage or "candidate_detail",
                "evidence_stage": target_stage or "candidate_detail",
                "rationale": "Repeat breaker: similar searches already happened, so convert search effort into candidate reading.",
                "checklist_status": node.inputs.get("checklist_status", []),
                "planner_suggested_action": node.action,
                "planner_suggested_rationale": node.inputs.get("rationale", ""),
                "multimodal_planning_used": node.inputs.get("multimodal_planning_used", False),
            },
            depends_on=node.depends_on,
            success_criteria=["action_ok", "evidence_or_fields"],
        )
    if has_successful_deep_read(traces):
        return WorkflowNode(
            id=f"d{step_id}",
            type="agent_dynamic_guarded",
            instruction="已有深读证据，不再继续搜相似内容，先输出当前结论。",
            action="summarize_text",
            inputs={
                "source": source,
                "dynamic": True,
                "requirement_slot": target_stage or "summary",
                "evidence_stage": target_stage or "summary",
                "rationale": "Repeat breaker: candidate pages were already read, so produce a grounded summary instead of repeating search.",
                "checklist_status": node.inputs.get("checklist_status", []),
                "planner_suggested_action": node.action,
                "planner_suggested_rationale": node.inputs.get("rationale", ""),
                "multimodal_planning_used": node.inputs.get("multimodal_planning_used", False),
            },
            depends_on=node.depends_on,
            success_criteria=["action_ok", "evidence_or_fields"],
        )
    return None


def apply_progress_guard(
    node: WorkflowNode,
    observation: Observation,
    traces: List[Dict[str, Any]],
    step_id: int,
    source: str,
    preferred_stage: str,
    fallback_stage: str,
) -> WorkflowNode | None:
    if node.action not in {"search_web", "wait", "scroll", "extract_page"}:
        return None
    current_target_stage = str(node.inputs.get("requirement_slot") or node.inputs.get("evidence_stage") or preferred_stage or fallback_stage or "")
    if (
        node.action in {"search_web", "wait", "scroll"}
        and has_candidate_links(observation)
        and not low_quality_current_page(observation, current_target_stage)
    ):
        next_action = "deep_read_candidates" if has_successful_collect_links(traces) and not has_deep_read_step(traces) else "open_candidate"
        return WorkflowNode(
            id=f"d{step_id}",
            type="agent_dynamic_guarded",
            instruction="已有候选链接，优先进入候选页面而不是继续等待、滚动或重复搜索。",
            action=next_action,
            inputs={
                "source": source,
                "dynamic": True,
                "rank": 0,
                "limit": 3,
                "requirement_slot": current_target_stage or "candidate_detail",
                "evidence_stage": current_target_stage or "candidate_detail",
                "rationale": (
                    "Progress guard: candidate links are already available, so open or read them before waiting, "
                    "scrolling, or issuing another search."
                ),
                "checklist_status": node.inputs.get("checklist_status", []),
                "planner_suggested_action": node.action,
                "planner_suggested_rationale": node.inputs.get("rationale", ""),
                "multimodal_planning_used": node.inputs.get("multimodal_planning_used", False),
            },
            depends_on=node.depends_on,
            success_criteria=["action_ok", "evidence_or_fields"],
        )
    if low_quality_current_page(observation, current_target_stage):
        return WorkflowNode(
            id=f"d{step_id}",
            type="agent_dynamic_guarded",
            instruction="当前页质量不足以继续深挖，优先返回搜索/结果页并重新抽取更可靠候选。",
            action="search_web",
            inputs={
                "source": source,
                "dynamic": True,
                "query": node.inputs.get("query") or query_from_observation_url(observation),
                "requirement_slot": current_target_stage or "candidate_pool",
                "evidence_stage": current_target_stage or "candidate_pool",
                "rationale": "Progress guard: current page looks low-quality or off-task for the target requirement slot.",
                "checklist_status": node.inputs.get("checklist_status", []),
                "planner_suggested_action": node.action,
                "planner_suggested_rationale": node.inputs.get("rationale", ""),
                "multimodal_planning_used": node.inputs.get("multimodal_planning_used", False),
            },
            depends_on=node.depends_on,
            success_criteria=["action_ok", "evidence_or_fields"],
        )
    if not looks_like_results_page(observation) or has_post_search_evidence_step(traces):
        return None
    if has_candidate_links(observation):
        return WorkflowNode(
            id=f"d{step_id}",
            type="agent_dynamic_guarded",
            instruction="当前已经到达搜索/结果页，先抽取候选链接或启用垂直候选恢复。",
            action="collect_links",
            inputs={
                "source": source,
                "dynamic": True,
                "query": query_from_observation_url(observation) or node.inputs.get("query"),
                "requirement_slot": node.inputs.get("requirement_slot") or preferred_stage or fallback_stage or "candidate_pool",
                "evidence_stage": node.inputs.get("evidence_stage") or preferred_stage or fallback_stage or "candidate_pool",
                "rationale": (
                    "Progress guard: current page is already a results/search page, so collect visible candidates "
                    "before issuing another search or wait."
                ),
                "checklist_status": node.inputs.get("checklist_status", []),
                "planner_suggested_action": node.action,
                "planner_suggested_rationale": node.inputs.get("rationale", ""),
                "multimodal_planning_used": node.inputs.get("multimodal_planning_used", False),
            },
            depends_on=node.depends_on,
            success_criteria=["action_ok", "evidence_or_fields"],
        )
    return WorkflowNode(
        id=f"d{step_id}",
        type="agent_dynamic_guarded",
        instruction="当前已经到达搜索/结果页，先抽取候选链接或启用垂直候选恢复。",
        action="collect_links",
        inputs={
            "source": source,
            "dynamic": True,
            "query": query_from_observation_url(observation) or node.inputs.get("query"),
            "requirement_slot": node.inputs.get("requirement_slot") or preferred_stage or fallback_stage or "candidate_pool",
            "evidence_stage": node.inputs.get("evidence_stage") or preferred_stage or fallback_stage or "candidate_pool",
            "rationale": (
                "Progress guard: current page is already a results/search page, so collect visible candidates "
                "before issuing another search or wait."
            ),
            "checklist_status": node.inputs.get("checklist_status", []),
            "planner_suggested_action": node.action,
            "planner_suggested_rationale": node.inputs.get("rationale", ""),
            "multimodal_planning_used": node.inputs.get("multimodal_planning_used", False),
        },
        depends_on=node.depends_on,
        success_criteria=["action_ok", "evidence_or_fields"],
    )
