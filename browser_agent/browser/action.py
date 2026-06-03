from __future__ import annotations

from typing import Any, Dict

from browser_agent.types import Action, Observation


TOOL_OUTCOMES = {
    "search": "collected candidate pages",
    "collect": "captured candidate cards",
    "open_topk": "opened top ranked detail pages",
    "compare": "produced comparison table and recommendation",
    "summarize": "summarized the page evidence",
    "analyze_form": "identified required form fields",
    "fill_form": "filled form draft values",
    "verify": "verified browser state against expected result",
    "find_slots": "found bookable time slots",
    "apply_filters": "applied user filters",
    "reserve": "created reservation draft pending confirmation",
    "extract_leads": "extracted structured lead records",
    "export_csv": "exported results to csv-ready rows",
    "snapshot_page": "captured baseline snapshot",
    "track_price": "registered watch target and threshold",
    "set_alert": "configured notification rule",
    "assert_ui": "validated critical UI checkpoints",
    "report_bug": "prepared regression report",
}


def execute_action(action: Action, observation: Observation) -> Dict[str, Any]:
    """Dispatch one browser tool action in a deterministic harness-safe mode."""
    outcome = TOOL_OUTCOMES.get(action.tool)
    if outcome is None:
        return {"ok": False, "tool": action.tool, "error": "unsupported_tool"}

    detail = {
        "message": outcome,
        "target": action.target,
        "value": action.value,
        "page_title": observation.title,
    }
    return {
        "ok": True,
        "tool": action.tool,
        "url": observation.url,
        "detail": detail,
    }
