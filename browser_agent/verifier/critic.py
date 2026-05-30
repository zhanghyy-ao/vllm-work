from __future__ import annotations

from typing import Any, Dict

from browser_agent.types import ActionResult, Observation, VerificationResult, WorkflowNode


def verify_step(tool: str, output: Dict[str, Any], observation: Observation) -> Dict[str, Any]:
    """Backward-compatible verification wrapper."""
    _ = observation
    ok = bool(output.get("ok"))
    evidence = output.get("evidence") or []
    checks = [
        {"name": "action_ok", "pass": ok},
        {"name": "evidence_or_fields", "pass": bool(evidence or output.get("fields"))},
    ]
    return {
        "ok": ok and all(check["pass"] for check in checks),
        "tool": tool,
        "reason": "verified" if ok else "tool_failed",
        "checks": checks,
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
