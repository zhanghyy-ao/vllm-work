from __future__ import annotations

from typing import Any, Dict


def summarize_metrics(run_result: Dict[str, Any]) -> Dict[str, float]:
    steps = run_result.get("steps", [])
    if not steps:
        return {"task_success": 0.0, "step_accuracy": 0.0}
    ok_steps = sum(1 for step in steps if step.get("ok"))
    return {
        "task_success": 1.0 if ok_steps == len(steps) else 0.0,
        "step_accuracy": ok_steps / len(steps),
    }
