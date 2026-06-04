from __future__ import annotations

from typing import Any, Dict

from browser_agent.types import ActionResult, Observation, VerificationResult, WorkflowNode


EXPECTED_TOOLS = {
    "search",
    "collect",
    "open_topk",
    "compare",
    "summarize",
    "analyze_form",
    "fill_form",
    "verify",
    "find_slots",
    "apply_filters",
    "reserve",
    "extract_leads",
    "export_csv",
    "snapshot_page",
    "track_price",
    "set_alert",
    "assert_ui",
    "report_bug",
}


def verify_step(tool: str, output: Dict[str, Any], observation: Observation) -> Dict[str, Any]:
    """Backward-compatible verification wrapper for deterministic actions."""
    _ = observation
    if tool not in EXPECTED_TOOLS:
        return {"ok": False, "tool": tool, "reason": "unknown_tool"}
    ok = bool(output.get("ok"))
    return {
        "ok": ok,
        "tool": tool,
        "reason": "basic_ok" if ok else output.get("error", "tool_failed"),
    }


def verify_node(node: WorkflowNode, result: ActionResult, observation: Observation) -> VerificationResult:
    """Validate one workflow node result before memory writeback."""
    _ = observation
    checks = [
        {"name": "action_ok", "pass": result.ok, "detail": result.error or "ok"},
        {"name": "page_reachable", "pass": bool(result.url), "detail": result.url},
        {
            "name": "evidence_or_fields",
            "pass": bool(result.evidence or result.fields),
            "detail": f"evidence={len(result.evidence)} fields={len(result.fields)}",
        },
    ]
    if node.action in {"collect_links", "summarize_text", "extract_video", "deep_read_candidates"}:
        checks.append(
            {
                "name": "content_non_empty",
                "pass": bool(
                    result.text
                    or result.fields.get("links")
                    or result.fields.get("summary")
                    or result.fields.get("video_digest")
                    or result.fields.get("deep_reads")
                ),
                "detail": "content extracted",
            }
        )
    passed = all(check["pass"] for check in checks)
    score = sum(1 for check in checks if check["pass"]) / len(checks)
    retry_hint = None
    if not passed:
        if not result.url:
            retry_hint = "retry_navigation"
        elif not (result.evidence or result.fields):
            retry_hint = "retry_extract"
        else:
            retry_hint = "retry_action"
    return VerificationResult(ok=passed, score=score, checks=checks, retry_hint=retry_hint)
