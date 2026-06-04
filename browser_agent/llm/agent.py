from __future__ import annotations

import json
from typing import Any, Dict, List
from urllib.parse import parse_qs, unquote_plus, urlparse

from browser_agent.llm.client import LLMClient, compact_evidence
from browser_agent.strategy.research_patterns import default_search_plan
from browser_agent.types import Observation, WorkflowNode, WorkflowSpec


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



def plan_next_action(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
    client: LLMClient | None,
    step_id: int,
) -> Dict[str, Any]:
    """Choose the next browser action from current page state and memory.

    This is the observation-driven agent loop path. Human-authored workflow
    nodes are treated as an evidence checklist/reference plan, not as the fixed
    execution order.
    """
    if client is None or not client.enabled:
        return {"ok": False, "reason": "llm_disabled_or_api_key_missing"}
    system = (
        "You are an observation-driven browser agent. Return strict JSON only. "
        "At each turn choose exactly one safe next action based on the current page observation, memory, "
        "completed steps, and evidence checklist. Do not follow a fixed script if the page state suggests a better next step. "
        "Do not reveal hidden chain-of-thought; provide only a short rationale and checklist_status. "
        "Never choose sensitive actions such as purchase, reserve, submit, login, payment, account changes, or form submission."
    )
    user = json.dumps(
        {
            "goal": workflow.goal,
            "domain": workflow.domain,
            "step_id": step_id,
            "current_page": _compact_observation(observation),
            "memory": {
                "evidence": compact_evidence(memory_dump.get("evidence", []), limit=16),
                "recent_traces": _compact_traces(memory_dump.get("traces", []), limit=8),
                "loop_state": _loop_state(memory_dump.get("traces", [])),
            },
            "completed_steps": _compact_steps(step_outputs[-8:]),
            "evidence_checklist": _contextual_evidence_checklist(
                workflow,
                observation,
                memory_dump,
                step_outputs,
            ),
            "available_actions": [
                {
                    "action": "goto",
                    "required_inputs": {"url": "absolute URL"},
                    "when_to_use": "open a known safe starting page or source page",
                },
                {
                    "action": "search_web",
                    "required_inputs": {"query": "targeted query", "source": "github|paper|shopping|video|general"},
                    "when_to_use": "fill a missing evidence stage with a targeted search",
                },
                {
                    "action": "collect_links",
                    "required_inputs": {"source": "github|paper|shopping|video|general"},
                    "when_to_use": "current page is a search/results page and candidate links should be extracted",
                },
                {
                    "action": "open_candidate",
                    "required_inputs": {"source": "github|paper|shopping|video|general", "rank": 0},
                    "when_to_use": "open a candidate link already stored in observation.elements",
                },
                {
                    "action": "click_element",
                    "required_inputs": {"element_ref": "element_id from interactable_elements"},
                    "when_to_use": "click a visible safe button/link/input from the current page",
                },
                {
                    "action": "type_text",
                    "required_inputs": {"element_ref": "textbox/searchbox element_id", "text": "text to type", "clear": True},
                    "when_to_use": "type into a visible text field; never enter passwords or credentials",
                },
                {
                    "action": "select_option",
                    "required_inputs": {"element_ref": "select element_id", "value": "option value"},
                    "when_to_use": "choose a visible select/dropdown option",
                },
                {
                    "action": "scroll",
                    "required_inputs": {"direction": "up|down", "pixels": 700},
                    "when_to_use": "more page content is likely below or above",
                },
                {
                    "action": "wait",
                    "required_inputs": {"ms": 1000},
                    "when_to_use": "wait briefly for dynamic content",
                },
                {
                    "action": "back",
                    "required_inputs": {},
                    "when_to_use": "return to previous page when current page is unhelpful",
                },
                {
                    "action": "press_key",
                    "required_inputs": {"key": "Enter|Escape|Tab"},
                    "when_to_use": "use safe keyboard navigation, often after typing into search fields",
                },
                {
                    "action": "deep_read_candidates",
                    "required_inputs": {"source": "github|paper|shopping|video|general", "limit": 3},
                    "when_to_use": "enough candidate links exist and deeper page evidence is needed",
                },
                {
                    "action": "extract_page",
                    "required_inputs": {"source": "github|paper|shopping|video|general"},
                    "when_to_use": "current page itself contains useful evidence",
                },
                {
                    "action": "extract_video",
                    "required_inputs": {"source": "video", "max_keyframes": 3},
                    "when_to_use": "current page is a video page or video result page with visible video metadata",
                },
                {
                    "action": "summarize_text",
                    "required_inputs": {"source": "github|paper|shopping|video|general"},
                    "when_to_use": "all required evidence is sufficiently covered and final synthesis can begin",
                },
                {
                    "action": "stop",
                    "required_inputs": {},
                    "when_to_use": "task is complete or cannot safely proceed",
                },
            ],
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
        decision = _apply_progress_guard(decision, workflow, observation, memory_dump, step_id)
    if decision.get("ok") and _decision_repeats(decision["node"], memory_dump.get("traces", [])):
        return {"ok": False, "reason": "loop_detected_repeated_action"}
    return decision


def _apply_progress_guard(
    decision: Dict[str, Any],
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_id: int,
) -> Dict[str, Any]:
    """Keep the dynamic planner moving from search pages into evidence collection.

    LLMs sometimes respond to partially rendered search pages by waiting or
    issuing another broad search. Mature browser agents usually add a controller
    policy around the planner: once a search/results page is reached, collect or
    extract current evidence before spending more turns on another search.
    """
    node = decision.get("node")
    if not isinstance(node, WorkflowNode):
        return decision
    if node.action not in {"search_web", "wait"}:
        return decision
    traces = memory_dump.get("traces", [])
    if _has_successful_collect_links(traces) and _has_candidate_links(observation) and not _has_deep_read_step(traces):
        guarded_inputs = {
            "source": node.inputs.get("source") or workflow.domain or "general",
            "dynamic": True,
            "limit": 3,
            "evidence_stage": node.inputs.get("evidence_stage") or _first_missing_stage(workflow) or "candidate_detail",
            "rationale": (
                "Progress guard: candidate links are already available, so read candidate pages before waiting "
                "or issuing another search."
            ),
            "checklist_status": node.inputs.get("checklist_status", []),
            "planner_suggested_action": node.action,
            "planner_suggested_rationale": node.inputs.get("rationale", ""),
            "multimodal_planning_used": node.inputs.get("multimodal_planning_used", False),
        }
        guarded = WorkflowNode(
            id=f"d{step_id}",
            type="agent_dynamic_guarded",
            instruction="已有候选链接，进入候选页面深读并抽取证据。",
            action="deep_read_candidates",
            inputs=guarded_inputs,
            depends_on=node.depends_on,
            success_criteria=["action_ok", "evidence_or_fields"],
        )
        return {**decision, "node": guarded, "progress_guard_applied": True}
    if not _looks_like_results_page(observation):
        return decision
    if _has_post_search_evidence_step(traces):
        return decision

    guarded_inputs = {
        "source": node.inputs.get("source") or workflow.domain or "general",
        "dynamic": True,
        "query": node.inputs.get("query") or _query_from_observation_url(observation),
        "evidence_stage": node.inputs.get("evidence_stage") or _first_missing_stage(workflow) or "candidate_pool",
        "rationale": (
            "Progress guard: current page is already a results/search page, so collect visible candidates "
            "before issuing another search or wait."
        ),
        "checklist_status": node.inputs.get("checklist_status", []),
        "planner_suggested_action": node.action,
        "planner_suggested_rationale": node.inputs.get("rationale", ""),
        "multimodal_planning_used": node.inputs.get("multimodal_planning_used", False),
    }
    guarded = WorkflowNode(
        id=f"d{step_id}",
        type="agent_dynamic_guarded",
        instruction="当前已经到达搜索/结果页，先抽取候选链接或启用垂直候选恢复。",
        action="collect_links",
        inputs=guarded_inputs,
        depends_on=node.depends_on,
        success_criteria=["action_ok", "evidence_or_fields"],
    )
    return {**decision, "node": guarded, "progress_guard_applied": True}


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
    if source not in {"github", "paper", "shopping", "video", "general"}:
        source = workflow.domain if workflow.domain in {"github", "paper", "shopping", "video"} else "general"
    normalized_inputs: Dict[str, Any] = {"source": source}
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
        inputs={
            **normalized_inputs,
            "dynamic": True,
            "rationale": str(result.get("rationale") or ""),
            "checklist_status": result.get("checklist_status") if isinstance(result.get("checklist_status"), list) else [],
        },
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


def _loop_state(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    visited_urls = []
    search_queries = []
    failed_actions = []
    for trace in traces:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        inputs = node.get("inputs") if isinstance(node.get("inputs"), dict) else {}
        output = trace.get("output") if isinstance(trace.get("output"), dict) else {}
        verdict = trace.get("verdict") if isinstance(trace.get("verdict"), dict) else {}
        if output.get("url"):
            visited_urls.append(output["url"])
        if node.get("action") == "search_web" and inputs.get("query"):
            search_queries.append(inputs["query"])
        if verdict.get("ok") is False:
            failed_actions.append({"action": node.get("action"), "reason": output.get("error")})
    return {
        "visited_urls": _dedupe_strings(visited_urls)[-12:],
        "search_queries": _dedupe_strings(search_queries)[-8:],
        "failed_actions": failed_actions[-5:],
        "repeat_warning": "Avoid repeating visited URLs, identical queries, or failed actions unless new evidence is expected.",
    }


def _dedupe_strings(values: List[Any]) -> List[str]:
    seen = set()
    out = []
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _decision_repeats(node: WorkflowNode, traces: List[Dict[str, Any]]) -> bool:
    same = 0
    for trace in traces[-4:]:
        prior = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        prior_inputs = prior.get("inputs") if isinstance(prior.get("inputs"), dict) else {}
        if prior.get("action") != node.action:
            continue
        if node.action == "search_web" and prior_inputs.get("query") == node.inputs.get("query"):
            same += 1
        elif node.action in {"click_element", "type_text", "select_option"} and str(prior_inputs.get("element_ref")) == str(node.inputs.get("element_ref")):
            same += 1
        elif node.action in {"scroll", "wait", "extract_page"}:
            same += 1
    return same >= 2


def _looks_like_results_page(observation: Observation) -> bool:
    parsed = urlparse(observation.url or "")
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if "bing.com" in host and ("/search" in path or "/videos/search" in path):
        return True
    if "github.com" in host and "/search" in path:
        return True
    if "arxiv.org" in host and "/search" in path:
        return True
    title_text = f"{observation.title} {observation.text[:500]}".lower()
    return any(term in title_text for term in ["search results", "搜索结果", "repositories", "论文", "视频搜索"])


def _query_from_observation_url(observation: Observation) -> str:
    parsed = urlparse(observation.url or "")
    query = parse_qs(parsed.query).get("q") or parse_qs(parsed.query).get("query") or [""]
    return unquote_plus(str(query[0]))[:300]


def _has_post_search_evidence_step(traces: List[Dict[str, Any]]) -> bool:
    seen_search = False
    for trace in traces:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        verdict = trace.get("verdict") if isinstance(trace.get("verdict"), dict) else {}
        action = node.get("action")
        if action == "search_web" and verdict.get("ok") is not False:
            seen_search = True
            continue
        if seen_search and action in {"collect_links", "open_candidate", "deep_read_candidates", "extract_page", "extract_video"}:
            return True
    return False


def _has_candidate_links(observation: Observation) -> bool:
    for item in observation.elements or []:
        if not isinstance(item, dict):
            continue
        href = str(item.get("href") or item.get("url") or "")
        if href.startswith("http://") or href.startswith("https://"):
            return True
    return False


def _has_deep_read_step(traces: List[Dict[str, Any]]) -> bool:
    for trace in traces:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        if node.get("action") in {"deep_read_candidates", "open_candidate", "extract_video"}:
            return True
    return False


def _has_successful_collect_links(traces: List[Dict[str, Any]]) -> bool:
    for trace in traces:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        output = trace.get("output") if isinstance(trace.get("output"), dict) else {}
        verdict = trace.get("verdict") if isinstance(trace.get("verdict"), dict) else {}
        fields = output.get("fields") if isinstance(output.get("fields"), dict) else {}
        if node.get("action") == "collect_links" and verdict.get("ok") is not False and isinstance(fields.get("links"), list) and fields["links"]:
            return True
    return False


def _first_missing_stage(workflow: WorkflowSpec) -> str:
    checklist = _evidence_checklist(workflow)
    if checklist:
        return str(checklist[0].get("stage") or "")
    return ""


def _contextual_evidence_checklist(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    checklist = _evidence_checklist(workflow)
    evidence = memory_dump.get("evidence", []) if isinstance(memory_dump, dict) else []
    traces = memory_dump.get("traces", []) if isinstance(memory_dump, dict) else []
    completed_stages = _completed_evidence_stages(step_outputs, traces)
    current_page_text = " ".join(
        [
            str(observation.url or ""),
            str(observation.title or ""),
            str(observation.text or "")[:1200],
            str(observation.visual_summary or ""),
        ]
    ).lower()
    evidence_text = " ".join(
        [
            str(item.get("claim") or "")
            for item in evidence
            if isinstance(item, dict)
        ]
        + [
            str(item.get("support") or "")
            for item in evidence
            if isinstance(item, dict)
        ]
    ).lower()
    contextual: List[Dict[str, Any]] = []
    for item in checklist:
        stage = str(item.get("stage") or "")
        status = "missing"
        notes: List[str] = []
        if stage in completed_stages:
            status = "satisfied"
            notes.append(f"已有执行步骤明确覆盖 `{stage}`。")
        elif _stage_visible_on_current_page(stage, current_page_text, observation):
            status = "partial"
            notes.append("当前页面已经出现相关线索，但还没有完成稳定提取。")
        elif _stage_present_in_evidence(stage, evidence_text):
            status = "partial"
            notes.append("memory 中已有相关证据片段，但覆盖度还不稳定。")
        else:
            notes.append(f"仍需补充 `{stage}` 相关证据。")
        contextual.append(
            {
                **item,
                "status": status,
                "evidence": " ".join(notes).strip(),
            }
        )
    return contextual


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


def _completed_evidence_stages(step_outputs: List[Dict[str, Any]], traces: List[Dict[str, Any]]) -> set[str]:
    stages: set[str] = set()
    for step in step_outputs:
        detail = step.get("detail") if isinstance(step.get("detail"), dict) else {}
        fields = detail.get("fields") if isinstance(detail.get("fields"), dict) else {}
        node_stage = str(fields.get("evidence_stage") or "")
        if step.get("ok") and node_stage:
            stages.add(node_stage)
    for trace in traces:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        inputs = node.get("inputs") if isinstance(node.get("inputs"), dict) else {}
        verdict = trace.get("verdict") if isinstance(trace.get("verdict"), dict) else {}
        stage = str(inputs.get("evidence_stage") or "")
        if verdict.get("ok") and stage:
            stages.add(stage)
    return stages


def _stage_present_in_evidence(stage: str, evidence_text: str) -> bool:
    hints = {
        "candidate_pool": ["candidate", "候选", "型号", "price", "价格"],
        "marketplace_pages": ["product page", "商品页", "官方", "参数", "销量", "京东", "天猫"],
        "comparative_reviews": ["compare", "comparison", "review", "评测", "对比", "缺点"],
        "user_comments": ["user", "comment", "complaint", "评论", "差评", "佩戴", "故障"],
        "video_reviews": ["video", "youtube", "bilibili", "视频", "字幕", "评论区"],
        "repo_candidates": ["repo", "repository", "github"],
        "repo_metadata": ["stars", "forks", "license", "updated"],
        "implementation_docs": ["readme", "installation", "example", "documentation"],
        "ecosystem_comparison": ["alternative", "benchmark", "comparison", "竞品"],
        "seed_papers": ["paper", "arxiv", "论文"],
        "related_work": ["survey", "related work", "benchmark", "综述"],
        "reproducibility": ["code", "dataset", "github", "复现"],
        "limitations": ["limitation", "failure", "局限", "失败"],
        "video_candidates": ["video", "tutorial", "教程"],
        "transcript_notes": ["transcript", "notes", "字幕", "笔记"],
        "visual_evidence": ["slide", "screen", "visual", "演示", "关键帧"],
        "comments_discussion": ["comment", "discussion", "评论", "讨论"],
        "orientation": ["overview", "background", "概览", "背景"],
        "primary_sources": ["official", "documentation", "官方"],
        "cross_validation": ["compare", "alternative", "limitations", "对比"],
    }
    return any(token in evidence_text for token in hints.get(stage, []))


def _stage_visible_on_current_page(stage: str, current_page_text: str, observation: Observation) -> bool:
    if stage == "candidate_pool":
        return len(observation.elements or []) >= 1 or _looks_like_results_page(observation)
    if stage == "marketplace_pages":
        return any(token in current_page_text for token in ["product", "商品", "参数", "京东", "天猫", "官方"])
    if stage == "comparative_reviews":
        return any(token in current_page_text for token in ["review", "compare", "评测", "对比"])
    if stage == "user_comments":
        return any(token in current_page_text for token in ["comment", "user review", "评论", "差评", "故障", "complaint"])
    if stage == "video_reviews":
        return any(token in current_page_text for token in ["video", "youtube", "bilibili", "视频"])
    if stage == "repo_candidates":
        return "github" in current_page_text and len(observation.elements or []) >= 1
    if stage == "repo_metadata":
        return any(token in current_page_text for token in ["stars", "forks", "license"])
    if stage == "implementation_docs":
        return any(token in current_page_text for token in ["readme", "installation", "example"])
    if stage == "ecosystem_comparison":
        return any(token in current_page_text for token in ["alternative", "comparison", "benchmark"])
    if stage == "seed_papers":
        return any(token in current_page_text for token in ["arxiv", "paper", "论文"])
    if stage == "related_work":
        return any(token in current_page_text for token in ["survey", "related", "benchmark"])
    if stage == "reproducibility":
        return any(token in current_page_text for token in ["code", "dataset", "github"])
    if stage == "limitations":
        return any(token in current_page_text for token in ["limitation", "failure", "局限"])
    if stage == "video_candidates":
        return "video" in current_page_text or "视频" in current_page_text
    if stage == "transcript_notes":
        return any(token in current_page_text for token in ["transcript", "chapter", "字幕", "章节"])
    if stage == "visual_evidence":
        return any(token in current_page_text for token in ["slide", "screen", "演示", "关键帧"])
    if stage == "comments_discussion":
        return any(token in current_page_text for token in ["comment", "discussion", "评论", "讨论"])
    if stage == "primary_sources":
        return any(token in current_page_text for token in ["official", "documentation", "官方"])
    if stage == "cross_validation":
        return any(token in current_page_text for token in ["alternative", "comparison", "limitations", "对比"])
    return False


def _evidence_checklist(workflow: WorkflowSpec) -> List[Dict[str, Any]]:
    stages: Dict[str, Dict[str, Any]] = {}
    for item in default_search_plan(workflow.domain, workflow.goal):
        stage = str(item.get("evidence_stage") or item.get("purpose") or "").strip()
        if not stage:
            continue
        stages.setdefault(
            stage,
            {
                "stage": stage,
                "purpose": item.get("purpose"),
                "suggested_source": item.get("source"),
                "example_query": item.get("query"),
            },
        )
    for node in workflow.nodes:
        stage = str(node.inputs.get("evidence_stage") or "").strip()
        if not stage:
            continue
        stages.setdefault(
            stage,
            {
                "stage": stage,
                "purpose": node.inputs.get("llm_purpose") or node.instruction,
                "suggested_source": node.inputs.get("source"),
                "example_query": node.inputs.get("query"),
            },
        )
    return list(stages.values())[:8]


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
                    "evidence_stage": _infer_evidence_stage(item, workflow.domain),
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
                    "evidence_stage": str(item.get("evidence_stage") or _infer_evidence_stage(item, workflow.domain)),
                }
            )
    items = _augment_search_plan(items, workflow.domain, workflow.goal)
    return _dedupe_search_plan(items, limit=_search_plan_limit(workflow.domain, result.get("task_type", "")))


def _search_plan_limit(domain: str, task_type: Any) -> int:
    text = str(task_type).lower()
    if domain == "shopping" or text in {"comparison", "recommendation"}:
        return 6
    if domain in {"github", "paper", "video"}:
        return 5
    return 4


def _infer_evidence_stage(item: Dict[str, Any], domain: str) -> str:
    stage = str(item.get("evidence_stage") or item.get("stage") or "").strip()
    if stage:
        return stage
    text = " ".join(str(item.get(key, "")) for key in ["query", "purpose", "source"]).lower()
    if domain == "shopping":
        if any(token in text for token in ["video", "youtube", "b站", "bilibili", "视频"]):
            return "video_reviews"
        if any(token in text for token in ["comment", "complaint", "差评", "用户", "评论", "佩戴", "夹头"]):
            return "user_comments"
        if any(token in text for token in ["京东", "天猫", "商品页", "official", "product page", "参数", "销量"]):
            return "marketplace_pages"
        if any(token in text for token in ["compare", "comparison", "对比", "评测", "review", "缺点"]):
            return "comparative_reviews"
        return "candidate_pool"
    if domain == "github":
        if any(token in text for token in ["readme", "install", "example", "documentation", "文档", "安装"]):
            return "implementation_docs"
        if any(token in text for token in ["star", "fork", "license", "updated", "维护", "许可证"]):
            return "repo_metadata"
        if any(token in text for token in ["alternative", "comparison", "benchmark", "竞品", "对比"]):
            return "ecosystem_comparison"
        return "repo_candidates"
    if domain == "paper":
        if any(token in text for token in ["code", "dataset", "github", "复现", "数据集"]):
            return "reproducibility"
        if any(token in text for token in ["survey", "benchmark", "related", "综述", "相关工作"]):
            return "related_work"
        if any(token in text for token in ["limitation", "failure", "evaluation", "局限", "失败", "评测"]):
            return "limitations"
        return "seed_papers"
    if domain == "video":
        if any(token in text for token in ["transcript", "chapter", "notes", "字幕", "章节", "笔记"]):
            return "transcript_notes"
        if any(token in text for token in ["demo", "slide", "screen", "visual", "演示", "屏幕", "幻灯片"]):
            return "visual_evidence"
        if any(token in text for token in ["comment", "discussion", "评论", "讨论"]):
            return "comments_discussion"
        return "video_candidates"
    if any(token in text for token in ["official", "documentation", "primary", "官方", "一手"]):
        return "primary_sources"
    if any(token in text for token in ["compare", "alternative", "limitation", "对比", "限制"]):
        return "cross_validation"
    return "orientation"


def _augment_search_plan(items: List[Dict[str, str]], domain: str, goal: str) -> List[Dict[str, str]]:
    required = default_search_plan(domain, goal)
    seen_stages = {str(item.get("evidence_stage", "")) for item in items}
    augmented = list(items)
    for fallback in required:
        stage = str(fallback.get("evidence_stage", ""))
        if stage and stage in seen_stages:
            continue
        augmented.append(
            {
                "query": str(fallback["query"]).strip(),
                "purpose": str(fallback.get("purpose") or stage or f"collect {domain} evidence"),
                "source": str(fallback.get("source") or domain),
                "evidence_stage": stage,
            }
        )
        if stage:
            seen_stages.add(stage)
    stage_order = {
        "candidate_pool": 0,
        "marketplace_pages": 1,
        "comparative_reviews": 2,
        "user_comments": 3,
        "video_reviews": 4,
        "repo_candidates": 0,
        "repo_metadata": 1,
        "implementation_docs": 2,
        "ecosystem_comparison": 3,
        "seed_papers": 0,
        "related_work": 1,
        "reproducibility": 2,
        "limitations": 3,
        "video_candidates": 0,
        "transcript_notes": 1,
        "visual_evidence": 2,
        "comments_discussion": 3,
        "orientation": 0,
        "primary_sources": 1,
        "cross_validation": 2,
    }
    return sorted(augmented, key=lambda item: stage_order.get(str(item.get("evidence_stage", "")), 9))


def _dedupe_search_plan(items: List[Dict[str, str]], limit: int) -> List[Dict[str, str]]:
    seen = set()
    deduped: List[Dict[str, str]] = []
    for item in items:
        key = (item["query"].lower(), item["source"], item.get("evidence_stage", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped



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
    report_max_tokens = getattr(client.config, "report_max_tokens", 1600)
    report_retry_max_tokens = getattr(client.config, "report_retry_max_tokens", 900)
    report_timeout_sec = max(8, min(18, int(getattr(client, "timeout_sec", 30) or 30)))
    result = _chat_json_compat(
        client,
        system,
        user,
        temperature=0.2,
        max_tokens=report_max_tokens,
        timeout_sec=report_timeout_sec,
    )
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
        result = _chat_json_compat(
            client,
            system,
            retry_user,
            temperature=0.0,
            max_tokens=report_retry_max_tokens,
            timeout_sec=max(6, report_timeout_sec - 4),
        )
    if not result.get("ok"):
        return {"used": False, "reason": result.get("error", "llm_report_failed")}
    return {"used": True, "report": result}


def _chat_json_compat(
    client: LLMClient,
    system: str,
    user: str,
    temperature: float,
    max_tokens: int,
    timeout_sec: int | None = None,
) -> Dict[str, Any]:
    try:
        return client.chat_json(system, user, temperature=temperature, max_tokens=max_tokens, timeout_sec=timeout_sec)
    except TypeError:
        return client.chat_json(system, user, temperature=temperature)


def _chat_json_with_image_compat(
    client: LLMClient,
    system: str,
    user: str,
    image_path: str,
    temperature: float,
    max_tokens: int,
) -> Dict[str, Any]:
    try:
        return client.chat_json_with_image(
            system,
            user,
            image_path=image_path,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except TypeError:
        return client.chat_json_with_image(system, user, image_path=image_path, temperature=temperature)


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
