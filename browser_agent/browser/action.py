from __future__ import annotations

from typing import Any, Dict

from browser_agent.types import Action, Observation


def execute_action(action: Action, observation: Observation) -> Dict[str, Any]:
    """Dispatch one browser tool action.

    Current version is harness-safe stub for architecture validation.
    """
    if action.tool in {"search", "collect", "open_topk", "compare", "summarize", "analyze_form", "fill_form", "verify"}:
        return {"ok": True, "tool": action.tool, "value": action.value, "url": observation.url}
    return {"ok": False, "tool": action.tool, "error": "unsupported_tool"}
