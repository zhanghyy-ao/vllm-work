from __future__ import annotations

from typing import Any, Dict

from browser_agent.types import Observation


def verify_step(tool: str, output: Dict[str, Any], observation: Observation) -> Dict[str, Any]:
    """Minimal verification layer.

    Future version should include DOM/vision consistency checks.
    """
    _ = observation
    ok = bool(output.get("ok"))
    return {"ok": ok, "tool": tool, "reason": "basic_ok" if ok else "tool_failed"}
