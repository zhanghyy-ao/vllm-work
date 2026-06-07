from __future__ import annotations

from typing import Any, Dict, List


RECOGNITION_ERROR_TOKENS = {
    "element_ref_not_found",
    "candidate_not_found",
    "candidate_missing_href",
    "no_candidates_to_deep_read",
    "no_links_collected",
    "no_video_metadata_extracted",
    "empty_page_text",
    "no_text_to_summarize",
    "missing_text",
    "missing_option_value",
}

PLANNING_ERROR_TOKENS = {
    "dynamic_plan_failed",
    "json_parse_failed",
    "unsupported_dynamic_action",
    "search_web_requires_query",
    "goto_requires_absolute_url",
    "press_key_not_allowed",
    "type_text_requires_text",
    "select_option_requires_value",
    "llm_disabled_or_api_key_missing",
}


def classify_failure_type(
    ok: bool,
    action: str,
    detail: Dict[str, Any] | None = None,
    fallback_used: str | None = None,
    planning_reason: str | None = None,
) -> str:
    if ok:
        return ""
    detail = detail or {}
    error_text = " ".join(
        [
            str(detail.get("error") or ""),
            str(detail.get("reason") or ""),
            str(planning_reason or ""),
            str(fallback_used or ""),
        ]
    ).lower()
    if any(token in error_text for token in PLANNING_ERROR_TOKENS):
        return "planning_failure"
    if any(token in error_text for token in RECOGNITION_ERROR_TOKENS):
        return "recognition_failure"
    if action in {"extract_page", "collect_links", "open_candidate", "deep_read_candidates", "extract_video"} and not detail.get("fields"):
        return "recognition_failure"
    return "execution_failure"


def summarize_failure_types(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts = {
        "recognition_failure": 0,
        "planning_failure": 0,
        "execution_failure": 0,
    }
    failed_steps = 0
    for step in steps:
        failure_type = str(step.get("failure_type") or "")
        if not step.get("ok"):
            failed_steps += 1
            if failure_type in counts:
                counts[failure_type] += 1
            elif failure_type:
                counts[failure_type] = counts.get(failure_type, 0) + 1
    return {
        "failed_steps": failed_steps,
        "failure_type_counts": counts,
    }
