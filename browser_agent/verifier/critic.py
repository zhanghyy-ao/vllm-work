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

SLOT_SIGNAL_FIELD_MAP = {
    "candidate_pool": "candidate_pool_signals",
    "repo_candidates": "repo_candidate_signals",
    "video_candidates": "video_candidate_signals",
    "repo_metadata": "repo_metadata_signals",
    "implementation_docs": "implementation_doc_signals",
    "comparative_reviews": "review_signals",
    "ecosystem_comparison": "comparison_signals",
    "marketplace_pages": "marketplace_signals",
    "user_comments": "comment_signals",
    "transcript_notes": "transcript_signals",
    "visual_evidence": "visual_signals",
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
    requirement_slot = str(node.inputs.get("requirement_slot") or node.inputs.get("evidence_stage") or "")
    if requirement_slot:
        slot_pass = _slot_signal_present(requirement_slot, result)
        checks.append(
            {
                "name": "requirement_slot_signal",
                "pass": slot_pass,
                "detail": requirement_slot,
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


def _slot_signal_present(requirement_slot: str, result: ActionResult) -> bool:
    text = f"{result.title} {result.text} {result.url}".lower()
    fields = result.fields if isinstance(result.fields, dict) else {}
    if fields.get("requirement_slot") == requirement_slot or fields.get("evidence_stage") == requirement_slot:
        signal_field = SLOT_SIGNAL_FIELD_MAP.get(requirement_slot, "requirement_slot_signals")
        signal_payload = fields.get(signal_field)
        if _structured_signal_present(requirement_slot, signal_payload):
            return True
        if signal_payload:
            return True
    if requirement_slot in {"candidate_pool", "repo_candidates", "video_candidates"}:
        return bool(fields.get("links") or result.evidence)
    hints = {
        "repo_metadata": ["stars", "forks", "license", "updated"],
        "implementation_docs": ["readme", "installation", "example", "documentation"],
        "comparative_reviews": ["review", "compare", "评测", "对比"],
        "user_comments": ["comment", "评论", "complaint", "差评"],
        "transcript_notes": ["transcript", "字幕", "chapter", "章节"],
        "visual_evidence": ["screenshot", "screen", "slide", "关键帧"],
    }
    return any(token in text for token in hints.get(requirement_slot, [])) or bool(result.evidence)


def _structured_signal_present(requirement_slot: str, signal_payload: Any) -> bool:
    if not isinstance(signal_payload, dict):
        return False
    if requirement_slot in {"candidate_pool", "repo_candidates", "video_candidates"}:
        return bool(signal_payload.get("candidates"))
    if requirement_slot == "repo_metadata":
        return bool(signal_payload.get("repositories") or signal_payload.get("readings"))
    if requirement_slot == "implementation_docs":
        return bool(signal_payload.get("doc_coverage") or signal_payload.get("doc_sources") or signal_payload.get("readings"))
    if requirement_slot in {"comparative_reviews", "ecosystem_comparison", "marketplace_pages"}:
        return bool(signal_payload.get("readings") or signal_payload.get("candidate_count"))
    if requirement_slot == "user_comments":
        return bool(signal_payload.get("comment_pages") or signal_payload.get("comment_signal") or signal_payload.get("readings"))
    if requirement_slot == "transcript_notes":
        return bool(signal_payload.get("transcript_excerpt") or signal_payload.get("video_title"))
    if requirement_slot == "visual_evidence":
        return bool(signal_payload.get("screenshot_path") or signal_payload.get("has_visual_summary"))
    return bool(signal_payload)
