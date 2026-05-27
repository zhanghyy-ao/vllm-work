from __future__ import annotations

import uuid
from time import time
from typing import Any, Dict, List

from browser_agent.browser.observer import observe
from browser_agent.harness.events import make_event
from browser_agent.harness.tool_dispatch import dispatch
from browser_agent.memory.session import SessionMemory
from browser_agent.planner.tot import plan_goal
from browser_agent.verifier.critic import verify_step


class HarnessRuntime:
    """Harness-first runtime loop.

    observe -> plan -> execute -> verify -> memory_writeback
    """

    def __init__(self, max_steps: int = 8) -> None:
        self.max_steps = max_steps

    def run(self, goal: str, start_url: str) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        memory = SessionMemory(goal=goal)
        observation = observe(start_url)
        plan = plan_goal(goal, observation)
        events: List[Dict[str, Any]] = []
        step_outputs: List[Dict[str, Any]] = []

        for idx, action in enumerate(plan.actions[: self.max_steps], start=1):
            started = time()
            output = dispatch(action, observation)
            verdict = verify_step(action.tool, output, observation)
            memory.write(action.tool, output, verdict)
            event = make_event(
                run_id=run_id,
                step_id=idx,
                phase="execute_verify",
                tool=action.tool,
                payload={"reason": action.reason, "target": action.target, "value": action.value},
                output={"result": output, "verdict": verdict},
                url=observation.url,
                start=started,
            )
            events.append(event.to_dict())
            step_outputs.append({"action": action.tool, "ok": verdict["ok"], "detail": output})
            if not verdict["ok"]:
                break

        return {
            "run_id": run_id,
            "goal": goal,
            "start_url": start_url,
            "plan": {
                "summary": plan.summary,
                "confidence": plan.confidence,
                "actions": [a.__dict__ for a in plan.actions],
            },
            "steps": step_outputs,
            "memory": memory.dump(),
            "events": events,
            "ok": all(step["ok"] for step in step_outputs) if step_outputs else False,
        }
