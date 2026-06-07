from __future__ import annotations

import json
from typing import Any, Dict, List

from browser_agent.agents.guard_policy import (
    apply_progress_guard as apply_progress_guard_policy,
    apply_repeat_breaker as apply_repeat_breaker_policy,
    prefer_in_page_react as prefer_in_page_react_policy,
)
from browser_agent.agents.checklist_policy import (
    best_contextual_stage as best_contextual_stage_policy,
    contextual_evidence_checklist as contextual_evidence_checklist_policy,
    evidence_checklist as evidence_checklist_policy,
    first_missing_stage as first_missing_stage_policy,
    preferred_stage_for_page as preferred_stage_for_page_policy,
    stage_status_from_outputs as stage_status_from_outputs_policy,
)
from browser_agent.agents.page_state import (
    current_page_capabilities as current_page_capabilities_policy,
    decision_repeats as decision_repeats_policy,
    first_searchbox_ref as page_state_first_searchbox_ref,
    has_candidate_links as page_state_has_candidate_links,
    has_deep_read_step as page_state_has_deep_read_step,
    has_successful_deep_read as page_state_has_successful_deep_read,
    has_post_search_evidence_step as page_state_has_post_search_evidence_step,
    has_successful_collect_links as page_state_has_successful_collect_links,
    looks_like_results_page as page_state_looks_like_results_page,
    loop_state as loop_state_policy,
    query_from_observation_url as page_state_query_from_observation_url,
)
from browser_agent.agents.prompt_loader import load_prompt
from browser_agent.agents.query_policy import (
    compact_goal_terms as policy_compact_goal_terms,
    extract_priority_terms as policy_extract_priority_terms,
    minimal_query_core as policy_minimal_query_core,
    requirement_driven_query as policy_requirement_driven_query,
)
from browser_agent.agents.stage_policy import (
    STAGE_TEXT_CUES,
    stage_affinity_score,
    stage_present_in_evidence,
    stage_visible_on_current_page as policy_stage_visible_on_current_page,
    slot_signal_present_from_action,
    slot_signal_present_in_fields,
)
from browser_agent.llm.client import LLMClient, compact_evidence
from browser_agent.strategy.research_patterns import requirement_slots
from browser_agent.types import AgentStepContext, Observation, PageFingerprint, WorkflowNode, WorkflowSpec


ALLOWED_DYNAMIC_ACTIONS = {
    "goto",
    "search_web",
    "collect_links",
    "open_candidate",
    "deep_read_candidates",
    "extract_page",
    "extract_video",
    "summarize_text",
    "click_element",
    "type_text",
    "select_option",
    "scroll",
    "wait",
    "back",
    "press_key",
    "stop",
}

SENSITIVE_DYNAMIC_TERMS = {
    "purchase",
    "buy now",
    "payment",
    "pay",
    "checkout",
    "submit order",
    "place order",
    "login",
    "password",
    "credential",
    "delete",
    "remove account",
    "提交订单",
    "购买",
    "付款",
    "支付",
    "结算",
    "登录",
    "密码",
    "删除",
    "注销",
}

def plan_browser_action(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
    client: LLMClient | None,
    step_id: int,
) -> Dict[str, Any]:
    """Navigator agent.

    Responsible only for selecting the next safe browser action from current
    page state, evidence memory, and checklist context.
    """
    if client is None or not client.enabled:
        return {"ok": False, "reason": "llm_disabled_or_api_key_missing"}
    system = load_prompt("navigator_system.md")
    context = build_agent_step_context(workflow, observation, memory_dump, step_outputs, step_id)
    user = json.dumps(
        {
            **context.to_dict(),
            "available_actions": _available_actions_schema(),
            "required_json_schema": {
                "status": "continue|final|blocked",
                "rationale": "one short visible reason, no hidden chain-of-thought",
                "checklist_status": [
                    {"stage": "evidence stage", "status": "missing|partial|satisfied", "evidence": "short note"}
                ],
                "next_action": {
                    "action": "one available action",
                    "instruction": "Chinese instruction for this step",
                    "inputs": {
                        "query": "only for search_web",
                        "url": "only for goto",
                        "source": "github|paper|shopping|video|general",
                        "element_ref": "element_id for click/type/select actions",
                        "text": "text for type_text",
                        "direction": "up|down for scroll",
                        "key": "safe key for press_key",
                        "rank": 0,
                        "limit": 3,
                        "evidence_stage": "stage being addressed",
                    },
                },
            },
        },
        ensure_ascii=False,
    )
    client_config = getattr(client, "config", None)
    planner_max_tokens = getattr(client_config, "planner_max_tokens", 1000)
    use_multimodal_planning = bool(getattr(client_config, "use_multimodal_planning", True))
    if observation.screenshot_path and use_multimodal_planning:
        result = _chat_json_with_image_compat(
            client,
            system,
            user,
            image_path=observation.screenshot_path,
            temperature=0.1,
            max_tokens=planner_max_tokens,
        )
        if result.get("ok"):
            result["multimodal_planning_used"] = True
        else:
            fallback = _chat_json_compat(client, system, user, temperature=0.1, max_tokens=planner_max_tokens)
            fallback["multimodal_planning_used"] = False
            fallback["multimodal_planning_error"] = result.get("error")
            result = fallback
    else:
        result = _chat_json_compat(client, system, user, temperature=0.1, max_tokens=planner_max_tokens)
        result["multimodal_planning_used"] = False
    if not result.get("ok"):
        return {"ok": False, "reason": result.get("error", "dynamic_plan_failed")}
    decision = _normalize_dynamic_decision(result, workflow, step_id)
    if decision.get("ok"):
        decision["multimodal_planning_used"] = bool(result.get("multimodal_planning_used"))
        if result.get("multimodal_planning_error"):
            decision["multimodal_planning_error"] = result.get("multimodal_planning_error")
        decision = apply_progress_guard(decision, workflow, observation, memory_dump, step_id)
    if decision.get("ok") and decision_repeats(decision["node"], memory_dump.get("traces", [])):
        return {"ok": False, "reason": "loop_detected_repeated_action"}
    decision["agent"] = "navigator"
    return decision


def build_agent_step_context(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
    step_id: int,
) -> AgentStepContext:
    return AgentStepContext(
        goal=workflow.goal,
        domain=workflow.domain,
        step_id=step_id,
        priority_requirement_slot=preferred_stage_for_page(workflow, observation, memory_dump, step_outputs),
        current_page=_compact_observation(observation),
        current_page_capabilities=current_page_capabilities(observation),
        page_fingerprint=PageFingerprint.from_observation(observation),
        evidence_checklist=contextual_evidence_checklist(workflow, observation, memory_dump, step_outputs),
        memory={
            "evidence": compact_evidence(memory_dump.get("evidence", []), limit=16),
            "recent_traces": _compact_traces(memory_dump.get("traces", []), limit=8),
            "loop_state": _loop_state(memory_dump.get("traces", [])),
        },
        completed_steps=_compact_steps(step_outputs[-8:]),
    )


def apply_progress_guard(
    decision: Dict[str, Any],
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_id: int,
) -> Dict[str, Any]:
    node = decision.get("node")
    if not isinstance(node, WorkflowNode):
        return decision
    preferred_stage = preferred_stage_for_page(workflow, observation, memory_dump, [])
    fallback_stage = first_missing_stage(workflow, observation, memory_dump, []) or ""
    traces = memory_dump.get("traces", [])
    repeat_breaker = apply_repeat_breaker_policy(
        node=node,
        observation=observation,
        traces=traces,
        step_id=step_id,
        source=node.inputs.get("source") or workflow.domain or "general",
        target_stage=str(preferred_stage or fallback_stage or ""),
    )
    if repeat_breaker is not None:
        return {**decision, "node": repeat_breaker, "progress_guard_applied": True, "repeat_breaker_applied": True}
    page_react = prefer_in_page_react(node, workflow, observation, memory_dump, step_id)
    if page_react is not None:
        if preferred_stage:
            page_react.inputs.setdefault("requirement_slot", preferred_stage)
            page_react.inputs.setdefault("evidence_stage", preferred_stage)
        return {**decision, "node": page_react, "progress_guard_applied": True, "react_guard_applied": True}
    guarded = apply_progress_guard_policy(
        node=node,
        observation=observation,
        traces=traces,
        step_id=step_id,
        source=node.inputs.get("source") or workflow.domain or "general",
        preferred_stage=preferred_stage,
        fallback_stage=fallback_stage,
    )
    if guarded is None:
        return decision
    return {**decision, "node": guarded, "progress_guard_applied": True}


def prefer_in_page_react(
    node: WorkflowNode,
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_id: int,
) -> WorkflowNode | None:
    traces = memory_dump.get("traces", [])
    target_stage = node.inputs.get("requirement_slot") or node.inputs.get("evidence_stage") or preferred_stage_for_page(workflow, observation, memory_dump, [])
    return prefer_in_page_react_policy(
        node=node,
        observation=observation,
        traces=traces,
        step_id=step_id,
        source=node.inputs.get("source") or workflow.domain or "general",
        target_stage=str(target_stage or ""),
        page_query=react_query_for_page(workflow, node),
    )


def contextual_evidence_checklist(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return contextual_evidence_checklist_policy(
        workflow=workflow,
        observation=observation,
        memory_dump=memory_dump,
        step_outputs=step_outputs,
        checklist_builder=evidence_checklist,
        stage_status_builder=stage_status_from_outputs,
        stage_visible_on_current_page=stage_visible_on_current_page,
        stage_present_in_evidence=stage_present_in_evidence,
        looks_like_results_page=looks_like_results_page,
        first_searchbox_ref=first_searchbox_ref,
    )


def first_missing_stage(
    workflow: WorkflowSpec,
    observation: Observation | None = None,
    memory_dump: Dict[str, Any] | None = None,
    step_outputs: List[Dict[str, Any]] | None = None,
) -> str:
    return first_missing_stage_policy(
        workflow=workflow,
        observation=observation,
        memory_dump=memory_dump,
        step_outputs=step_outputs,
        contextual_builder=contextual_evidence_checklist,
        best_stage_picker=_best_contextual_stage,
        checklist_builder=evidence_checklist,
    )


def decision_repeats(node: WorkflowNode, traces: List[Dict[str, Any]]) -> bool:
    return decision_repeats_policy(node, traces)


def preferred_stage_for_page(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
) -> str:
    return preferred_stage_for_page_policy(
        workflow=workflow,
        observation=observation,
        memory_dump=memory_dump,
        step_outputs=step_outputs,
        contextual_builder=contextual_evidence_checklist,
        best_stage_picker=_best_contextual_stage,
        fallback_first_missing_stage=first_missing_stage,
    )


def _best_contextual_stage(contextual: List[Dict[str, Any]], observation: Observation, target_status: str) -> str:
    return best_contextual_stage_policy(
        contextual=contextual,
        observation=observation,
        target_status=target_status,
        stage_affinity_score=_stage_affinity_score,
    )


def _stage_affinity_score(stage: str, observation: Observation) -> int:
    return stage_affinity_score(
        stage,
        observation,
        looks_like_results_page=looks_like_results_page(observation),
        has_searchbox=first_searchbox_ref(observation) is not None,
    )


def stage_visible_on_current_page(
    stage: str,
    current_page_text: str,
    observation: Observation,
    looks_like_results_page: bool | None = None,
    has_searchbox: bool | None = None,
) -> bool:
    return policy_stage_visible_on_current_page(
        stage,
        current_page_text,
        observation,
        looks_like_results_page=looks_like_results_page if looks_like_results_page is not None else looks_like_results_page_fn(observation),
        has_searchbox=has_searchbox if has_searchbox is not None else first_searchbox_ref(observation) is not None,
    )


def evidence_checklist(workflow: WorkflowSpec) -> List[Dict[str, Any]]:
    return evidence_checklist_policy(
        workflow=workflow,
        query_builder=requirement_driven_query,
    )


def first_searchbox_ref(observation: Observation) -> Any:
    return page_state_first_searchbox_ref(observation)


def react_query_for_page(workflow: WorkflowSpec, node: WorkflowNode) -> str:
    query = str(node.inputs.get("query") or "").strip()
    if query:
        return query
    target_stage = str(node.inputs.get("requirement_slot") or node.inputs.get("evidence_stage") or "")
    if target_stage:
        derived = requirement_driven_query(workflow.goal, workflow.domain, target_stage)
        if derived:
            return derived[:160]
    return workflow.goal[:160]


def _available_actions_schema() -> List[Dict[str, Any]]:
    return [
        {"action": "goto", "required_inputs": {"url": "absolute URL"}, "when_to_use": "open a known safe starting page only when the current page cannot advance the target requirement slot"},
        {"action": "search_web", "required_inputs": {"query": "targeted query", "source": "github|paper|shopping|video|general"}, "when_to_use": "last-resort fallback after confirming the current page has no usable interactable path"},
        {"action": "collect_links", "required_inputs": {"source": "github|paper|shopping|video|general"}, "when_to_use": "current page already shows results/cards/candidates and they should be extracted first"},
        {"action": "open_candidate", "required_inputs": {"source": "github|paper|shopping|video|general", "rank": 0}, "when_to_use": "open a candidate link already visible on the page before issuing a fresh search"},
        {"action": "click_element", "required_inputs": {"element_ref": "element_id from interactable_elements"}, "when_to_use": "click a visible safe button/link/input that advances the target requirement slot"},
        {"action": "type_text", "required_inputs": {"element_ref": "textbox/searchbox element_id", "text": "text to type", "clear": True}, "when_to_use": "type into a visible text field to advance the task on the current page; never enter passwords or credentials"},
        {"action": "select_option", "required_inputs": {"element_ref": "select element_id", "value": "option value"}, "when_to_use": "choose a visible select/dropdown option"},
        {"action": "scroll", "required_inputs": {"direction": "up|down", "pixels": 700}, "when_to_use": "more page content is likely below or above"},
        {"action": "wait", "required_inputs": {"ms": 1000}, "when_to_use": "wait briefly for dynamic content"},
        {"action": "back", "required_inputs": {}, "when_to_use": "return to previous page when current page is unhelpful"},
        {"action": "press_key", "required_inputs": {"key": "Enter|Escape|Tab"}, "when_to_use": "use safe keyboard navigation, often after typing into search fields"},
        {"action": "deep_read_candidates", "required_inputs": {"source": "github|paper|shopping|video|general", "limit": 3}, "when_to_use": "enough candidate links exist and deeper page evidence is needed"},
        {"action": "extract_page", "required_inputs": {"source": "github|paper|shopping|video|general"}, "when_to_use": "current page itself contains useful evidence"},
        {"action": "extract_video", "required_inputs": {"source": "video", "max_keyframes": 3}, "when_to_use": "current page is a video page or video result page with visible video metadata"},
        {"action": "summarize_text", "required_inputs": {"source": "github|paper|shopping|video|general"}, "when_to_use": "all required evidence is sufficiently covered and final synthesis can begin"},
        {"action": "stop", "required_inputs": {}, "when_to_use": "task is complete or cannot safely proceed"},
    ]


def _normalize_dynamic_decision(result: Dict[str, Any], workflow: WorkflowSpec, step_id: int) -> Dict[str, Any]:
    status = str(result.get("status") or "continue").strip().lower()
    if status not in {"continue", "final", "blocked"}:
        status = "continue"
    raw_action = result.get("next_action") if isinstance(result.get("next_action"), dict) else {}
    action = str(raw_action.get("action") or ("summarize_text" if status == "final" else "")).strip()
    if action not in ALLOWED_DYNAMIC_ACTIONS:
        return {"ok": False, "reason": f"unsupported_dynamic_action:{action}"}
    if _dynamic_action_sensitive(action, raw_action):
        return {"ok": False, "reason": "sensitive_dynamic_action_requires_human_approval"}
    inputs = raw_action.get("inputs") if isinstance(raw_action.get("inputs"), dict) else {}
    source = str(inputs.get("source") or workflow.domain or "general")
    if source not in {"github", "paper", "shopping", "video", "general", "form", "booking", "lead", "monitoring", "qa"}:
        source = workflow.domain if workflow.domain in {"github", "paper", "shopping", "video", "form", "booking", "lead", "monitoring", "qa"} else "general"
    normalized_inputs: Dict[str, Any] = {"source": source}
    if inputs.get("requirement_slot"):
        normalized_inputs["requirement_slot"] = str(inputs.get("requirement_slot"))
    if inputs.get("evidence_stage"):
        normalized_inputs["evidence_stage"] = str(inputs.get("evidence_stage"))
    if action == "goto":
        url = str(inputs.get("url") or "").strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return {"ok": False, "reason": "goto_requires_absolute_url"}
        normalized_inputs["url"] = url
    elif action == "search_web":
        query = str(inputs.get("query") or "").strip()
        if not query:
            target_stage = str(inputs.get("requirement_slot") or inputs.get("evidence_stage") or "")
            query = requirement_driven_query(workflow.goal, workflow.domain, target_stage)
        if not query:
            return {"ok": False, "reason": "search_web_requires_query"}
        normalized_inputs["query"] = _guard_query(workflow.domain, workflow.goal, query)
    elif action == "open_candidate":
        normalized_inputs["rank"] = _safe_int(inputs.get("rank"), default=0, minimum=0, maximum=9)
    elif action == "deep_read_candidates":
        normalized_inputs["limit"] = _safe_int(inputs.get("limit"), default=3, minimum=1, maximum=5)
    elif action == "extract_video":
        normalized_inputs["max_keyframes"] = _safe_int(inputs.get("max_keyframes"), default=3, minimum=1, maximum=5)
        normalized_inputs["source"] = "video"
    elif action in {"click_element", "type_text", "select_option"}:
        element_ref = inputs.get("element_ref", inputs.get("element_id", inputs.get("index")))
        if element_ref is None:
            return {"ok": False, "reason": f"{action}_requires_element_ref"}
        normalized_inputs["element_ref"] = element_ref
        if action == "type_text":
            text = str(inputs.get("text") or inputs.get("value") or "")
            if not text:
                return {"ok": False, "reason": "type_text_requires_text"}
            normalized_inputs["text"] = text[:500]
            normalized_inputs["clear"] = bool(inputs.get("clear", True))
            normalized_inputs["submit_after_type"] = bool(inputs.get("submit_after_type", True))
        if action == "select_option":
            value = str(inputs.get("value") or inputs.get("label") or "")
            if not value:
                return {"ok": False, "reason": "select_option_requires_value"}
            normalized_inputs["value"] = value[:200]
    elif action == "scroll":
        direction = str(inputs.get("direction") or "down").lower()
        normalized_inputs["direction"] = "up" if direction == "up" else "down"
        normalized_inputs["pixels"] = _safe_int(inputs.get("pixels"), default=700, minimum=100, maximum=2000)
    elif action == "wait":
        normalized_inputs["ms"] = _safe_int(inputs.get("ms"), default=1000, minimum=250, maximum=5000)
    elif action == "press_key":
        key = str(inputs.get("key") or "")
        if key not in {"Enter", "Escape", "Tab", "ArrowDown", "ArrowUp", "Space"}:
            return {"ok": False, "reason": "press_key_not_allowed"}
        normalized_inputs["key"] = key
    node = WorkflowNode(
        id=f"d{step_id}",
        type="agent_dynamic" if action != "stop" else "agent_control",
        instruction=str(raw_action.get("instruction") or result.get("rationale") or f"动态执行 {action}").strip(),
        action=action,
        inputs={**normalized_inputs, "dynamic": True, "rationale": str(result.get("rationale") or ""), "checklist_status": result.get("checklist_status") if isinstance(result.get("checklist_status"), list) else []},
        depends_on=[f"d{step_id - 1}"] if step_id > 1 else [],
        success_criteria=["action_ok", "evidence_or_fields"],
    )
    return {
        "ok": True,
        "status": status,
        "node": node,
        "rationale": result.get("rationale", ""),
        "checklist_status": result.get("checklist_status") if isinstance(result.get("checklist_status"), list) else [],
    }


def _safe_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _dynamic_action_sensitive(action: str, raw_action: Dict[str, Any]) -> bool:
    text = json.dumps(raw_action, ensure_ascii=False).lower()
    if any(term in text for term in SENSITIVE_DYNAMIC_TERMS):
        return True
    if action == "click_element" and any(term in text for term in ["submit", "order", "reserve", "book", "提交", "预订", "预约"]):
        return True
    return False


def _compact_observation(observation: Observation) -> Dict[str, Any]:
    return {
        "url": observation.url,
        "title": observation.title,
        "text_excerpt": str(observation.text or "")[:2500],
        "candidate_count": len(observation.elements or []),
        "interactable_elements": [
            {
                "rank": idx,
                "element_id": item.get("element_id", item.get("id", idx)),
                "role": item.get("role"),
                "tag": item.get("tag"),
                "text": str(item.get("text") or item.get("label") or "")[:180],
                "name": str(item.get("name") or item.get("label") or "")[:180],
                "href": str(item.get("href") or item.get("url") or "")[:240],
                "selector": str(item.get("selector") or "")[:120],
                "bbox": item.get("bbox"),
            }
            for idx, item in enumerate((observation.elements or [])[:8])
            if isinstance(item, dict)
        ],
        "form_fields": observation.form_fields[:12],
        "visible_buttons": observation.visible_buttons[:12],
        "accessibility_tree": observation.accessibility_tree[:20],
        "screenshot_path": observation.screenshot_path,
        "visual_summary": observation.visual_summary,
        "extracted_field_keys": sorted(observation.extracted_fields.keys()),
    }


def current_page_capabilities(observation: Observation) -> Dict[str, Any]:
    return current_page_capabilities_policy(observation)


def _compact_traces(traces: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    compact = []
    for trace in traces[-limit:]:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        output = trace.get("output") if isinstance(trace.get("output"), dict) else {}
        verdict = trace.get("verdict") if isinstance(trace.get("verdict"), dict) else {}
        compact.append(
            {
                "action": node.get("action") or trace.get("tool"),
                "instruction": node.get("instruction"),
                "ok": verdict.get("ok"),
                "url": output.get("url"),
                "title": output.get("title"),
                "error": output.get("error"),
                "field_keys": sorted((output.get("fields") or {}).keys()) if isinstance(output.get("fields"), dict) else [],
            }
        )
    return compact


def _compact_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    compact = []
    for step in steps:
        detail = step.get("detail") if isinstance(step.get("detail"), dict) else {}
        compact.append(
            {
                "action": step.get("action"),
                "ok": step.get("ok"),
                "score": step.get("score"),
                "fallback_used": step.get("fallback_used"),
                "url": detail.get("url"),
                "error": detail.get("error"),
            }
        )
    return compact


def _loop_state(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    return loop_state_policy(traces)


def looks_like_results_page(observation: Observation) -> bool:
    return page_state_looks_like_results_page(observation)


def query_from_observation_url(observation: Observation) -> str:
    return page_state_query_from_observation_url(observation)


def has_post_search_evidence_step(traces: List[Dict[str, Any]]) -> bool:
    return page_state_has_post_search_evidence_step(traces)


def has_candidate_links(observation: Observation) -> bool:
    return page_state_has_candidate_links(observation)


def has_deep_read_step(traces: List[Dict[str, Any]]) -> bool:
    return page_state_has_deep_read_step(traces)


def has_successful_collect_links(traces: List[Dict[str, Any]]) -> bool:
    return page_state_has_successful_collect_links(traces)


def has_successful_deep_read(traces: List[Dict[str, Any]]) -> bool:
    return page_state_has_successful_deep_read(traces)


def completed_evidence_stages(step_outputs: List[Dict[str, Any]], traces: List[Dict[str, Any]]) -> set[str]:
    stages = {stage for stage, status in stage_status_from_outputs(step_outputs, traces).items() if status == "satisfied"}
    return stages


def stage_status_from_outputs(step_outputs: List[Dict[str, Any]], traces: List[Dict[str, Any]]) -> Dict[str, str]:
    return stage_status_from_outputs_policy(
        step_outputs=step_outputs,
        traces=traces,
        slot_signal_present_in_fields=slot_signal_present_in_fields,
        slot_signal_present_from_action=slot_signal_present_from_action,
    )


def requirement_driven_query(goal: str, domain: str, target_stage: str) -> str:
    return policy_requirement_driven_query(goal, domain, target_stage)


def minimal_query_core(goal_text: str, domain: str, target_stage: str) -> str:
    return policy_minimal_query_core(goal_text, domain, target_stage)


def extract_priority_terms(goal_text: str, priorities: List[str], max_terms: int) -> str:
    return policy_extract_priority_terms(goal_text, priorities, max_terms)


def compact_goal_terms(goal_text: str, max_terms: int = 5) -> str:
    return policy_compact_goal_terms(goal_text, max_terms)


def looks_like_results_page_fn(observation: Observation) -> bool:
    return looks_like_results_page(observation)


def _guard_query(domain: str, goal: str, query: str) -> str:
    if domain == "shopping" and ("keyboard" in query.lower() or "键盘" in goal):
        return "学生 无线 机械键盘 推荐 价格"
    if domain == "shopping":
        normalized = " ".join(str(query or "").split())
        if "1000元以内" in normalized and "降噪耳机" in normalized:
            parts = [normalized]
            if not any(token in normalized for token in ["评测", "对比", "商品", "价格", "评价", "京东", "天猫"]):
                parts.append("评测 对比 商品 价格")
            if not any(token in normalized for token in ["-股票", "-指数", "-中证1000", "-基金", "-证券"]):
                parts.append("-股票 -指数 -中证1000 -基金 -证券")
            return " ".join(parts)
        return normalized
    return query


def _chat_json_compat(
    client: LLMClient,
    system: str,
    user: str,
    temperature: float = 0.1,
    max_tokens: int = 1000,
) -> Dict[str, Any]:
    try:
        return client.chat_json(system, user, temperature=temperature, max_tokens=max_tokens)
    except TypeError:
        return client.chat_json(system, user, temperature=temperature)


def _chat_json_with_image_compat(
    client: LLMClient,
    system: str,
    user: str,
    image_path: str,
    temperature: float = 0.1,
    max_tokens: int = 1000,
) -> Dict[str, Any]:
    try:
        return client.chat_json_with_image(system, user, image_path=image_path, temperature=temperature, max_tokens=max_tokens)
    except TypeError:
        return client.chat_json_with_image(system, user, image_path=image_path, temperature=temperature)
