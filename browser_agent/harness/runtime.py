from __future__ import annotations

import uuid
from time import time
from typing import Any, Dict, List

from browser_agent.browser.observer import observe
from browser_agent.evaluation.metrics import summarize_metrics
from browser_agent.harness.events import make_event
from browser_agent.harness.tool_dispatch import dispatch
from browser_agent.market.compare import compare_market_profiles
from browser_agent.memory.session import SessionMemory
from browser_agent.planner.tot import plan_goal
from browser_agent.verifier.critic import verify_step


class HarnessRuntime:
    """Harness-first runtime loop.

    observe -> plan -> execute -> verify -> memory_writeback
    """

    def __init__(
        self,
        max_steps: int = 8,
        auto_approve_sensitive: bool = False,
        include_market_comparison: bool = True,
    ) -> None:
        self.max_steps = max_steps
        self.auto_approve_sensitive = auto_approve_sensitive
        self.include_market_comparison = include_market_comparison

    def run(self, goal: str, start_url: str) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        memory = SessionMemory(goal=goal)
        observation = observe(start_url)
        plan = plan_goal(goal, observation)
        events: List[Dict[str, Any]] = []
        step_outputs: List[Dict[str, Any]] = []
        approval_requests: List[Dict[str, Any]] = []

        for idx, action in enumerate(plan.actions[: self.max_steps], start=1):
            started = time()
            if action.sensitive and not self.auto_approve_sensitive:
                output = {
                    "ok": False,
                    "tool": action.tool,
                    "status": "awaiting_user_approval",
                    "detail": {
                        "message": "Sensitive browser action paused pending approval.",
                        "target": action.target,
                        "value": action.value,
                        "page_title": observation.title,
                    },
                }
                verdict = {
                    "ok": False,
                    "tool": action.tool,
                    "reason": "awaiting_user_approval",
                }
                approval_requests.append(
                    {
                        "step_id": idx,
                        "tool": action.tool,
                        "reason": action.reason,
                        "target": action.target,
                    }
                )
            else:
                output = dispatch(action, observation)
                verdict = verify_step(action.tool, output, observation)
            memory.write(action.tool, output, verdict)
            event = make_event(
                run_id=run_id,
                step_id=idx,
                phase="execute_verify",
                tool=action.tool,
                payload={
                    "reason": action.reason,
                    "target": action.target,
                    "value": action.value,
                },
                output={"result": output, "verdict": verdict},
                url=observation.url,
                start=started,
            )
            events.append(event.to_dict())
            step_outputs.append(
                {
                    "action": action.tool,
                    "ok": verdict["ok"],
                    "sensitive": action.sensitive,
                    "detail": output,
                    "reason": verdict["reason"],
                }
            )
            if not verdict["ok"]:
                break

        ok = all(step["ok"] for step in step_outputs) if step_outputs else False
        evidence = self._build_evidence_summary(observation, plan, step_outputs)
        result = {
            "run_id": run_id,
            "goal": goal,
            "start_url": start_url,
            "scenario": plan.scenario,
            "plan": {
                "summary": plan.summary,
                "confidence": plan.confidence,
                "risk_level": plan.risk_level,
                "deliverable": plan.deliverable,
                "success_checks": plan.success_checks,
                "actions": [a.__dict__ for a in plan.actions],
            },
            "steps": step_outputs,
            "memory": memory.dump(),
            "events": events,
            "approval_requests": approval_requests,
            "evidence": evidence,
            "ok": ok,
        }
        if self.include_market_comparison:
            result["market_comparison"] = compare_market_profiles(plan.scenario)
        result["metrics"] = summarize_metrics(result)
        return result

    def _build_evidence_summary(
        self,
        observation: Any,
        plan: Any,
        step_outputs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "page_title": observation.title,
            "observed_url": observation.url,
            "scenario_risk": plan.risk_level,
            "planned_deliverable": plan.deliverable,
            "visible_element_labels": [item.get("label", "") for item in observation.elements[:5]],
            "executed_tools": [step["action"] for step in step_outputs],
            "successful_steps": sum(1 for step in step_outputs if step["ok"]),
        }
