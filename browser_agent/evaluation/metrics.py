from __future__ import annotations

from typing import Any, Dict, List

from browser_agent.strategy.research_patterns import default_search_plan


def summarize_metrics(run_result: Dict[str, Any]) -> Dict[str, float]:
    steps = run_result.get("steps", [])
    if not steps:
        return {
            "task_success": 0.0,
            "step_accuracy": 0.0,
            "checklist_coverage": 0.0,
            "final_answer_groundedness": 0.0,
            "source_citation_correctness": 0.0,
            "browser_state_goal_match": 0.0,
        }

    ok_steps = sum(1 for step in steps if step.get("ok"))
    if run_result.get("scenario") and not run_result.get("workflow"):
        return {
            "task_success": 1.0 if ok_steps == len(steps) else 0.0,
            "step_accuracy": ok_steps / len(steps),
            "checklist_coverage": 1.0,
            "final_answer_groundedness": 1.0,
            "source_citation_correctness": 1.0,
            "browser_state_goal_match": 1.0,
        }
    checklist_coverage = _checklist_coverage(run_result)
    groundedness = _groundedness(run_result)
    citation_correctness = _citation_correctness(run_result)
    browser_match = _browser_state_goal_match(run_result)
    return {
        "task_success": 1.0 if ok_steps == len(steps) and checklist_coverage >= 0.5 and groundedness >= 0.5 else 0.0,
        "step_accuracy": ok_steps / len(steps),
        "checklist_coverage": checklist_coverage,
        "final_answer_groundedness": groundedness,
        "source_citation_correctness": citation_correctness,
        "browser_state_goal_match": browser_match,
    }


def _checklist_coverage(run_result: Dict[str, Any]) -> float:
    workflow = run_result.get("workflow", {}) if isinstance(run_result.get("workflow"), dict) else {}
    domain = str(workflow.get("domain") or run_result.get("domain") or "general")
    goal = str(run_result.get("goal") or workflow.get("goal") or "")
    required = [str(item.get("evidence_stage")) for item in default_search_plan(domain, goal) if item.get("evidence_stage")]
    if not required:
        return 1.0
    seen = set()
    for step in run_result.get("steps", []):
        detail = step.get("detail", {}) if isinstance(step.get("detail"), dict) else {}
        fields = detail.get("fields", {}) if isinstance(detail.get("fields"), dict) else {}
        stage = fields.get("evidence_stage")
        if not stage:
            node = next((item for item in workflow.get("nodes", []) if item.get("id") == step.get("node_id")), {})
            inputs = node.get("inputs", {}) if isinstance(node.get("inputs"), dict) else {}
            stage = inputs.get("evidence_stage")
        if stage:
            seen.add(str(stage))
    return len([stage for stage in required if stage in seen]) / len(required)


def _groundedness(run_result: Dict[str, Any]) -> float:
    report = run_result.get("report", {}) if isinstance(run_result.get("report"), dict) else {}
    evidence = run_result.get("memory", {}).get("evidence", []) if isinstance(run_result.get("memory"), dict) else []
    summary = str(report.get("summary") or "")
    recommendations = report.get("recommendations") if isinstance(report.get("recommendations"), list) else []
    if not summary and not recommendations:
        return 0.0
    if evidence and (report.get("citations") or report.get("source_readings") or recommendations):
        return 1.0
    return 0.5 if evidence else 0.0


def _citation_correctness(run_result: Dict[str, Any]) -> float:
    report = run_result.get("report", {}) if isinstance(run_result.get("report"), dict) else {}
    citations = report.get("citations") if isinstance(report.get("citations"), list) else []
    if not citations:
        return 0.0
    valid = 0
    for item in citations:
        url = str(item.get("source_url") or "")
        if url.startswith("http://") or url.startswith("https://"):
            valid += 1
    return valid / len(citations)


def _browser_state_goal_match(run_result: Dict[str, Any]) -> float:
    goal = str(run_result.get("goal") or "").lower()
    if not goal:
        return 0.0
    haystack_parts: List[str] = []
    for step in run_result.get("steps", [])[-3:]:
        detail = step.get("detail", {}) if isinstance(step.get("detail"), dict) else {}
        haystack_parts.extend([str(detail.get("url") or ""), str(detail.get("title") or ""), str(detail.get("text") or "")[:500]])
    haystack = " ".join(haystack_parts).lower()
    terms = [term for term in goal.replace("，", " ").replace(",", " ").split() if len(term) >= 2]
    if not terms:
        return 0.0
    hits = sum(1 for term in terms[:12] if term.lower() in haystack)
    return min(1.0, hits / min(len(terms), 6))
