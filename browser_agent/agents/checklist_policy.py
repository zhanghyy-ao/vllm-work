from __future__ import annotations

from typing import Any, Callable, Dict, List

from browser_agent.strategy.research_patterns import requirement_slots
from browser_agent.types import Observation, WorkflowSpec


def evidence_checklist(
    workflow: WorkflowSpec,
    query_builder: Callable[[str, str, str], str],
) -> List[Dict[str, Any]]:
    stages: Dict[str, Dict[str, Any]] = {}
    for slot in requirement_slots(workflow.domain, workflow.goal):
        stage = str(slot.get("slot") or "").strip()
        if not stage:
            continue
        stages.setdefault(
            stage,
            {
                "stage": stage,
                "requirement_slot": stage,
                "purpose": slot.get("purpose"),
                "suggested_source": slot.get("source"),
                "example_query": query_builder(workflow.goal, workflow.domain, stage),
            },
        )
    for node in workflow.nodes:
        stage = str(node.inputs.get("requirement_slot") or node.inputs.get("evidence_stage") or "").strip()
        if not stage:
            continue
        stages.setdefault(stage, {"stage": stage, "requirement_slot": stage})
        stages[stage]["purpose"] = stages[stage].get("purpose") or node.inputs.get("llm_purpose") or node.instruction
        stages[stage]["suggested_source"] = stages[stage].get("suggested_source") or node.inputs.get("source")
        stages[stage]["example_query"] = stages[stage].get("example_query") or node.inputs.get("query") or query_builder(workflow.goal, workflow.domain, stage)
    return list(stages.values())[:8]


def stage_status_from_outputs(
    step_outputs: List[Dict[str, Any]],
    traces: List[Dict[str, Any]],
    slot_signal_present_in_fields: Callable[[str, Dict[str, Any]], bool],
    slot_signal_present_from_action: Callable[[str, Any, Dict[str, Any]], bool],
) -> Dict[str, str]:
    statuses: Dict[str, str] = {}
    for step in step_outputs:
        detail = step.get("detail") if isinstance(step.get("detail"), dict) else {}
        fields = detail.get("fields") if isinstance(detail.get("fields"), dict) else {}
        stage = str(fields.get("requirement_slot") or fields.get("evidence_stage") or "")
        if not stage:
            continue
        signal_present = slot_signal_present_in_fields(stage, fields)
        if step.get("ok") and (signal_present or slot_signal_present_from_action(stage, step.get("action"), fields)):
            statuses[stage] = "satisfied"
        elif statuses.get(stage) != "satisfied":
            statuses[stage] = "partial"
    for trace in traces:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        inputs = node.get("inputs") if isinstance(node.get("inputs"), dict) else {}
        output = trace.get("output") if isinstance(trace.get("output"), dict) else {}
        verdict = trace.get("verdict") if isinstance(trace.get("verdict"), dict) else {}
        fields = output.get("fields") if isinstance(output.get("fields"), dict) else {}
        stage = str(fields.get("requirement_slot") or fields.get("evidence_stage") or inputs.get("requirement_slot") or inputs.get("evidence_stage") or "")
        if not stage:
            continue
        signal_present = slot_signal_present_in_fields(stage, fields)
        action = node.get("action")
        if verdict.get("ok") and (signal_present or slot_signal_present_from_action(stage, action, fields)):
            statuses[stage] = "satisfied"
        elif statuses.get(stage) != "satisfied":
            statuses[stage] = "partial"
    return statuses


def contextual_evidence_checklist(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
    checklist_builder: Callable[[WorkflowSpec], List[Dict[str, Any]]],
    stage_status_builder: Callable[[List[Dict[str, Any]], List[Dict[str, Any]]], Dict[str, str]],
    stage_visible_on_current_page: Callable[[str, str, Observation, bool | None, bool | None], bool],
    stage_present_in_evidence: Callable[[str, str, Observation | None], bool],
    looks_like_results_page: Callable[[Observation], bool],
    first_searchbox_ref: Callable[[Observation], Any],
) -> List[Dict[str, Any]]:
    checklist = checklist_builder(workflow)
    evidence = memory_dump.get("evidence", []) if isinstance(memory_dump, dict) else []
    traces = memory_dump.get("traces", []) if isinstance(memory_dump, dict) else []
    stage_status_map = stage_status_builder(step_outputs, traces)
    current_page_text = " ".join(
        [
            str(observation.url or ""),
            str(observation.title or ""),
            str(observation.text or "")[:1200],
            str(observation.visual_summary or ""),
        ]
    ).lower()
    evidence_text = " ".join(
        [str(item.get("claim") or "") for item in evidence if isinstance(item, dict)]
        + [str(item.get("support") or "") for item in evidence if isinstance(item, dict)]
    ).lower()
    contextual: List[Dict[str, Any]] = []
    for item in checklist:
        stage = str(item.get("stage") or "")
        status = "missing"
        notes: List[str] = []
        structured_status = stage_status_map.get(stage)
        if structured_status == "satisfied":
            status = "satisfied"
            notes.append(f"已有结构化执行结果明确覆盖 `{stage}`。")
        elif structured_status == "partial":
            status = "partial"
            notes.append(f"已有结构化执行痕迹触达 `{stage}`，但还未稳定完成。")
        elif stage_visible_on_current_page(
            stage,
            current_page_text,
            observation,
            looks_like_results_page=looks_like_results_page(observation),
            has_searchbox=first_searchbox_ref(observation) is not None,
        ):
            status = "partial"
            notes.append("当前页面已经出现相关线索，但还没有完成稳定提取。")
        elif stage_present_in_evidence(stage, evidence_text, observation):
            status = "partial"
            notes.append("memory 中已有相关证据片段，但覆盖度还不稳定。")
        else:
            notes.append(f"仍需补充 `{stage}` 相关证据。")
        contextual.append({**item, "status": status, "evidence": " ".join(notes).strip()})
    return contextual


def best_contextual_stage(
    contextual: List[Dict[str, Any]],
    observation: Observation,
    target_status: str,
    stage_affinity_score: Callable[[str, Observation], int],
) -> str:
    candidates = [item for item in contextual if item.get("status") == target_status]
    if not candidates:
        return ""
    if target_status == "partial":
        strong_matches = [item for item in candidates if stage_affinity_score(str(item.get("stage") or ""), observation) >= 8]
        if strong_matches:
            candidates = strong_matches
        review_like = [item for item in candidates if str(item.get("stage") or "") in {"comparative_reviews", "user_comments", "repo_metadata", "implementation_docs"}]
        if review_like:
            candidates = review_like
    ranked = sorted(
        candidates,
        key=lambda item: stage_affinity_score(str(item.get("stage") or ""), observation),
        reverse=True,
    )
    return str(ranked[0].get("stage") or "")


def first_missing_stage(
    workflow: WorkflowSpec,
    observation: Observation | None,
    memory_dump: Dict[str, Any] | None,
    step_outputs: List[Dict[str, Any]] | None,
    contextual_builder: Callable[[WorkflowSpec, Observation, Dict[str, Any], List[Dict[str, Any]]], List[Dict[str, Any]]],
    best_stage_picker: Callable[[List[Dict[str, Any]], Observation, str], str],
    checklist_builder: Callable[[WorkflowSpec], List[Dict[str, Any]]],
) -> str:
    if observation is not None:
        contextual = contextual_builder(
            workflow,
            observation,
            memory_dump or {"evidence": [], "traces": []},
            step_outputs or [],
        )
        best_partial = best_stage_picker(contextual, observation, "partial")
        if best_partial:
            return best_partial
        best_missing = best_stage_picker(contextual, observation, "missing")
        if best_missing:
            return best_missing
    checklist = checklist_builder(workflow)
    if checklist:
        return str(checklist[0].get("stage") or "")
    return ""


def preferred_stage_for_page(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
    contextual_builder: Callable[[WorkflowSpec, Observation, Dict[str, Any], List[Dict[str, Any]]], List[Dict[str, Any]]],
    best_stage_picker: Callable[[List[Dict[str, Any]], Observation, str], str],
    fallback_first_missing_stage: Callable[[WorkflowSpec, Observation | None, Dict[str, Any] | None, List[Dict[str, Any]] | None], str],
) -> str:
    contextual = contextual_builder(workflow, observation, memory_dump, step_outputs)
    best_satisfied = best_stage_picker(contextual, observation, "satisfied")
    if best_satisfied:
        return best_satisfied
    best_partial = best_stage_picker(contextual, observation, "partial")
    if best_partial:
        return best_partial
    best_missing = best_stage_picker(contextual, observation, "missing")
    if best_missing:
        return best_missing
    return fallback_first_missing_stage(workflow, observation, memory_dump, step_outputs)
