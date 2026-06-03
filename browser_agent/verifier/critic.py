from __future__ import annotations

from typing import Any, Dict

from browser_agent.types import Observation


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
    """Minimal verification layer with tool allow-list checks."""
    _ = observation
    if tool not in EXPECTED_TOOLS:
        return {"ok": False, "tool": tool, "reason": "unknown_tool"}

    ok = bool(output.get("ok"))
    return {
        "ok": ok,
        "tool": tool,
        "reason": "basic_ok" if ok else "tool_failed",
    }
