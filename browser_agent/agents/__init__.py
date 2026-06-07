from __future__ import annotations

from typing import TYPE_CHECKING, Any

__all__ = ["build_report_payload", "plan_browser_action", "plan_next_step", "summarize_supervisor_state"]

if TYPE_CHECKING:
    from .navigator import plan_browser_action
    from .reporter import build_report_payload
    from .supervisor import plan_next_step, summarize_supervisor_state


def __getattr__(name: str) -> Any:
    if name == "plan_browser_action":
        from .navigator import plan_browser_action as value

        return value
    if name == "build_report_payload":
        from .reporter import build_report_payload as value

        return value
    if name == "plan_next_step":
        from .supervisor import plan_next_step as value

        return value
    if name == "summarize_supervisor_state":
        from .supervisor import summarize_supervisor_state as value

        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
