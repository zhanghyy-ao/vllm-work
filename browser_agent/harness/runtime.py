from __future__ import annotations

from dataclasses import replace
import uuid
from time import time
from typing import Any, Dict, List

from browser_agent.browser.action import BrowserSession
from browser_agent.config import AgentConfig, build_agent_config
from browser_agent.harness.events import make_event
from browser_agent.harness.tool_dispatch import dispatch_node
from browser_agent.llm.agent import build_llm_report, enhance_workflow_with_llm
from browser_agent.llm.client import LLMClient
from browser_agent.memory.session import SessionMemory
from browser_agent.output.report_builder import build_report
from browser_agent.planner.tot import plan_goal
from browser_agent.types import ActionResult, Observation, WorkflowNode
from browser_agent.verifier.critic import verify_node
from browser_agent.vision.keyframes import visual_inputs_from_video_digest
from browser_agent.vision.multimodal import GeminiVisionProvider, build_video_visual_prompt


class HarnessRuntime:
    """Harness-first workflow runtime.

    plan -> execute -> observe -> verify -> memory -> report
    """

    def __init__(self, max_steps: int = 8, headless: bool = True, agent_config: AgentConfig | None = None) -> None:
        self.max_steps = max_steps
        self.headless = headless
        self.agent_config = agent_config or build_agent_config()
        self.llm_client = LLMClient(self.agent_config)

    def run(self, goal: str, start_url: str, domain: str = "auto") -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        memory = SessionMemory(goal=goal)
        observation = Observation(url=start_url, title="", text="")
        workflow = plan_goal(goal, observation, domain=domain)
        llm_plan = enhance_workflow_with_llm(workflow, self.llm_client)
        events: List[Dict[str, Any]] = []
        step_outputs: List[Dict[str, Any]] = []

        try:
            with BrowserSession(headless=self.headless) as session:
                for idx, node in enumerate(workflow.nodes[: self.max_steps], start=1):
                    result, verdict, event_dict = self._execute_with_retries(
                        session=session,
                        run_id=run_id,
                        step_id=idx,
                        node=node,
                        observation=observation,
                    )
                    events.append(event_dict)
                    memory.write_node(node.to_dict(), result.to_dict(), verdict.to_dict())
                    observation = result.to_observation(observation)
                    step_outputs.append(
                        {
                            "node_id": node.id,
                            "action": node.action,
                            "ok": verdict.ok,
                            "score": verdict.score,
                            "fallback_used": result.fallback_used,
                            "detail": result.to_dict(),
                        }
                    )
                    if not verdict.ok and not result.fallback_used:
                        break
        except Exception as exc:
            failure = ActionResult(ok=False, action="browser_session", url=start_url, error=str(exc), human_review_required=True)
            step_outputs.append({"action": "browser_session", "ok": False, "detail": failure.to_dict()})

        memory_dump = memory.dump()
        artifact = build_report(workflow, memory_dump, step_outputs)
        self._attach_multimodal_analysis(workflow.goal, artifact)
        llm_report = build_llm_report(workflow, memory_dump, self.llm_client)
        if llm_report.get("used") and isinstance(llm_report.get("report"), dict):
            report_payload = llm_report["report"]
            if report_payload.get("summary"):
                artifact.summary = report_payload["summary"]
            if isinstance(report_payload.get("recommendations"), list) and report_payload["recommendations"]:
                artifact.recommendations = report_payload["recommendations"]
            if isinstance(report_payload.get("reasoning_outline"), list) and report_payload["reasoning_outline"]:
                artifact.reasoning_outline = report_payload["reasoning_outline"]
            if isinstance(report_payload.get("subquestions"), list) and report_payload["subquestions"]:
                artifact.subquestions = report_payload["subquestions"]
            if isinstance(report_payload.get("search_plan"), list) and report_payload["search_plan"]:
                artifact.search_plan = report_payload["search_plan"]
            if isinstance(report_payload.get("source_readings"), list) and report_payload["source_readings"]:
                artifact.source_readings = report_payload["source_readings"]
            if isinstance(report_payload.get("decision_criteria"), list) and report_payload["decision_criteria"]:
                artifact.decision_criteria = report_payload["decision_criteria"]
            if isinstance(report_payload.get("comparison_matrix"), list) and report_payload["comparison_matrix"]:
                artifact.comparison_matrix = report_payload["comparison_matrix"]
            if isinstance(report_payload.get("video_digest"), dict):
                artifact.video_digest = {**artifact.video_digest, **report_payload["video_digest"]}
            if isinstance(report_payload.get("multimodal_notes"), list) and report_payload["multimodal_notes"]:
                artifact.multimodal_notes = [*artifact.multimodal_notes, *report_payload["multimodal_notes"]]
            if isinstance(report_payload.get("uncertainties"), list) and report_payload["uncertainties"]:
                artifact.uncertainties = report_payload["uncertainties"]
            if isinstance(report_payload.get("next_actions"), list) and report_payload["next_actions"]:
                artifact.next_actions = report_payload["next_actions"]
        ok = bool(step_outputs) and all(step["ok"] for step in step_outputs)

        return {
            "run_id": run_id,
            "agent": self.agent_config.to_dict(),
            "llm": {
                "enabled": self.llm_client.enabled,
                "plan": llm_plan,
                "report": {"used": llm_report.get("used", False), "reason": llm_report.get("reason")},
            },
            "goal": goal,
            "start_url": start_url,
            "workflow": workflow.to_dict(),
            "plan": {
                "summary": workflow.summary,
                "confidence": workflow.confidence,
                "actions": [node.to_action().__dict__ for node in workflow.nodes],
            },
            "steps": step_outputs,
            "memory": memory_dump,
            "report": artifact.to_dict(),
            "events": events,
            "ok": ok,
        }

    def _attach_multimodal_analysis(self, goal: str, artifact) -> None:
        visual_inputs = visual_inputs_from_video_digest(artifact.video_digest)
        if not visual_inputs:
            return
        provider = GeminiVisionProvider(self.agent_config)
        known_context = " ".join(
            str(part)
            for part in [
                artifact.video_digest.get("title", ""),
                artifact.video_digest.get("visible_transcript", ""),
                artifact.summary,
            ]
            if part
        )
        prompt = build_video_visual_prompt(goal, known_context)
        analyses = []
        for visual_input in visual_inputs[:4]:
            result = provider.analyze_image(visual_input, prompt)
            analyses.append({"input": visual_input, **result})
        successful = [item for item in analyses if item.get("ok")]
        if successful:
            combined = "\n\n".join(str(item.get("text", "")) for item in successful if item.get("text"))
            artifact.video_digest["visual_analysis"] = combined
            artifact.video_digest["visual_inputs"] = visual_inputs
            artifact.multimodal_notes.append(
                {
                    "provider": "gemini",
                    "status": "available",
                    "input": visual_inputs,
                    "purpose": "视频页截图/关键帧视觉理解",
                    "finding": combined[:1000],
                }
            )
            return
        first = analyses[0] if analyses else {}
        artifact.video_digest["visual_inputs"] = visual_inputs
        artifact.multimodal_notes.append(
            {
                "provider": "gemini",
                "status": "unavailable",
                "input": visual_inputs,
                "purpose": "视频页截图/关键帧视觉理解",
                "reason": first.get("reason", "unknown"),
            }
        )

    def _execute_with_retries(
        self,
        session: BrowserSession,
        run_id: str,
        step_id: int,
        node: WorkflowNode,
        observation: Observation,
    ):
        max_retries = int(node.retry_policy.get("max_retries", 2))
        attempts = 0
        current = node
        last_result: ActionResult | None = None
        last_verdict = None
        started = time()

        while attempts <= max_retries:
            result = dispatch_node(session, current, observation)
            verdict = verify_node(current, result, observation)
            if verdict.ok:
                event = make_event(
                    run_id=run_id,
                    step_id=step_id,
                    phase="execute_verify",
                    tool=current.action,
                    payload={"node": current.to_dict(), "attempt": attempts + 1},
                    output={"result": result.to_dict(), "verdict": verdict.to_dict()},
                    url=result.url or observation.url,
                    start=started,
                )
                return result, verdict, event.to_dict()
            last_result = result
            last_verdict = verdict
            attempts += 1
            current = self._fallback_node(current, verdict.retry_hint, attempts)

        assert last_result is not None and last_verdict is not None
        event = make_event(
            run_id=run_id,
            step_id=step_id,
            phase="execute_verify_failed",
            tool=node.action,
            payload={"node": node.to_dict(), "attempts": attempts},
            output={"result": last_result.to_dict(), "verdict": last_verdict.to_dict()},
            url=last_result.url or observation.url,
            start=started,
        )
        return last_result, last_verdict, event.to_dict()

    def _fallback_node(self, node: WorkflowNode, retry_hint: str | None, attempt: int) -> WorkflowNode:
        inputs = dict(node.inputs)
        fallback = retry_hint or "retry_action"
        if node.action == "search_web" and attempt == 1:
            inputs["source"] = "general"
            fallback = "fallback_to_general_search"
        elif node.action == "collect_links":
            fallback = "fallback_to_extract_page"
            return replace(node, action="extract_page", inputs={**inputs, "fallback_used": fallback})
        return replace(node, inputs={**inputs, "fallback_used": fallback})
