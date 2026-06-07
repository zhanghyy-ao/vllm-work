from __future__ import annotations

import json
from typing import Any, Dict, List

from browser_agent.agents.navigator import plan_browser_action
from browser_agent.agents.prompt_loader import load_prompt
from browser_agent.llm.client import LLMClient, compact_evidence
from browser_agent.strategy.research_patterns import default_evidence_plan, default_search_plan, requirement_slots
from browser_agent.types import Observation, WorkflowSpec


def plan_next_action(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
    client: LLMClient | None,
    step_id: int,
) -> Dict[str, Any]:
    """Backward-compatible wrapper.

    New code should call the navigator or supervisor agents directly. This
    wrapper is kept so existing tests and imports continue to work during the
    migration.
    """
    return plan_browser_action(
        workflow=workflow,
        observation=observation,
        memory_dump=memory_dump,
        step_outputs=step_outputs,
        client=client,
        step_id=step_id,
    )


def build_llm_report(workflow: WorkflowSpec, memory_dump: Dict[str, Any], client: LLMClient | None) -> Dict[str, Any]:
    if client is None or not client.enabled:
        return {"used": False, "reason": "llm_disabled_or_api_key_missing"}
    evidence = compact_evidence(memory_dump.get("evidence", []))
    strategy = _workflow_strategy(workflow)
    system = load_prompt("reporter_system.md")
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
                "requirement_progression": [
                    {
                        "requirement_slot": "slot name",
                        "purpose": "why this slot matters",
                        "status": "missing|partial|satisfied",
                        "latest_action": "browser action used most recently for this slot",
                        "latest_url": "page used for this slot",
                        "evidence_summary": "Chinese evidence summary"
                    }
                ],
                "evidence_plan": [
                    {"evidence_hint": "intent or hint used to unlock evidence", "query": "legacy compatibility alias", "purpose": "evidence purpose", "source": "source type", "requirement_slot": "slot name"}
                ],
                "search_plan": [
                    {"evidence_hint": "legacy compatibility alias of evidence_plan", "query": "legacy compatibility alias", "purpose": "evidence purpose", "source": "source type"}
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
                "instruction": "Return only valid minified JSON with keys: summary, reasoning_outline, subquestions, requirement_progression, evidence_plan, search_plan, source_readings, recommendations, decision_criteria, comparison_matrix, video_digest, multimodal_notes, uncertainties, next_actions.",
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


def _workflow_strategy(workflow: WorkflowSpec) -> Dict[str, Any]:
    evidence_plan = []
    requirement_progression = []
    decision_criteria: List[Dict[str, Any]] = []
    subquestions: List[str] = []
    reasoning_outline: List[str] = []
    slot_index = {str(item.get("slot")): item for item in requirement_slots(workflow.domain, workflow.goal)}
    for node in workflow.nodes:
        slot = str(node.inputs.get("requirement_slot") or node.inputs.get("evidence_stage") or "").strip()
        if slot:
            requirement_progression.append(
                {
                    "requirement_slot": slot,
                    "purpose": node.inputs.get("llm_purpose") or slot_index.get(slot, {}).get("purpose") or node.instruction,
                    "status": "satisfied" if node.action in {"collect_links", "deep_read_candidates", "extract_page", "extract_video", "summarize_text"} else "partial",
                    "latest_action": node.action,
                    "latest_url": node.inputs.get("url") or "",
                    "evidence_summary": node.instruction,
                }
            )
        if node.action == "search_web":
            evidence_plan.append(
                {
                    "evidence_hint": node.inputs.get("query"),
                    "query": node.inputs.get("query"),
                    "purpose": node.inputs.get("llm_purpose"),
                    "source": node.inputs.get("source"),
                    "requirement_slot": slot,
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
        "requirement_progression": requirement_progression[:8],
        "evidence_plan": evidence_plan[:6],
        "search_plan": evidence_plan[:6],
    }


def _normalize_search_plan(result: Dict[str, Any], workflow: WorkflowSpec) -> List[Dict[str, Any]]:
    raw_plan = result.get("evidence_plan") if isinstance(result.get("evidence_plan"), list) else []
    if not raw_plan:
        raw_plan = result.get("search_plan") if isinstance(result.get("search_plan"), list) else []
    normalized: List[Dict[str, Any]] = []
    seen_slots = set()
    for item in raw_plan:
        if not isinstance(item, dict):
            continue
        slot = str(item.get("requirement_slot") or item.get("evidence_stage") or "").strip()
        normalized_item = {
            "evidence_hint": str(item.get("evidence_hint") or item.get("query") or "").strip(),
            "query": str(item.get("query") or item.get("evidence_hint") or "").strip(),
            "purpose": str(item.get("purpose") or "").strip(),
            "source": str(item.get("source") or workflow.domain or "general").strip(),
            "evidence_stage": slot,
            "requirement_slot": slot,
        }
        normalized.append(normalized_item)
        if slot:
            seen_slots.add(slot)
    for item in default_evidence_plan(workflow.domain, workflow.goal):
        slot = str(item.get("requirement_slot") or item.get("evidence_stage") or "").strip()
        if slot in seen_slots:
            continue
        normalized.append(
            {
                "evidence_hint": str(item.get("evidence_hint") or item.get("query") or "").strip(),
                "query": str(item.get("query") or item.get("evidence_hint") or "").strip(),
                "purpose": str(item.get("purpose") or "").strip(),
                "source": str(item.get("source") or workflow.domain or "general").strip(),
                "evidence_stage": slot,
                "requirement_slot": slot,
            }
        )
        if slot:
            seen_slots.add(slot)
    return normalized[:8]
