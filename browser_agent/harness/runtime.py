from __future__ import annotations

import uuid
from dataclasses import replace
from time import time
from typing import Any, Dict, List

from browser_agent.browser.action import BrowserSession, execute_action
from browser_agent.browser.observer import observe
from browser_agent.config import AgentConfig, build_agent_config
from browser_agent.evaluation.metrics import summarize_metrics
from browser_agent.harness.events import make_event
from browser_agent.harness.tool_dispatch import dispatch_node
from browser_agent.llm.agent import build_llm_report, plan_next_action
from browser_agent.llm.client import LLMClient
from browser_agent.market.compare import compare_market_profiles
from browser_agent.memory.session import SessionMemory
from browser_agent.output.report_builder import build_report
from browser_agent.planner.tot import detect_domain, plan_goal, plan_scenario_goal
from browser_agent.strategy.research_patterns import default_search_plan
from browser_agent.types import ActionResult, Observation, Plan, WorkflowNode
from browser_agent.verifier.critic import verify_node, verify_step
from browser_agent.vision.keyframes import visual_inputs_from_video_digest
from browser_agent.vision.multimodal import GeminiVisionProvider, build_video_visual_prompt


SCENARIO_ONLY_DOMAINS = {"form", "booking", "lead", "monitoring", "qa", "general"}


class HarnessRuntime:
    """Harness-first workflow runtime.

    The runtime supports two compatible paths:
    - full browser workflow for research/search/recommendation/video tasks;
    - deterministic scenario harness for booking, lead, monitoring and QA tasks.
    """

    def __init__(
        self,
        max_steps: int = 8,
        headless: bool = True,
        agent_config: AgentConfig | None = None,
        auto_approve_sensitive: bool = False,
        include_market_comparison: bool = True,
    ) -> None:
        self.max_steps = max_steps
        self.headless = headless
        self.agent_config = agent_config or build_agent_config()
        self.llm_client = LLMClient(self.agent_config)
        self.auto_approve_sensitive = auto_approve_sensitive
        self.include_market_comparison = include_market_comparison
        self._visual_summary_cache: Dict[str, str] = {}

    def run(self, goal: str, start_url: str, domain: str = "auto") -> Dict[str, Any]:
        if self._should_use_scenario_harness(goal, domain):
            return self._run_scenario(goal, start_url)
        return self._run_workflow(goal, start_url, domain=domain)

    def _should_use_scenario_harness(self, goal: str, domain: str) -> bool:
        if domain != "auto":
            return detect_domain(goal, domain) in SCENARIO_ONLY_DOMAINS
        scenario = plan_scenario_goal(goal, Observation(url="", title="", text=""))
        if scenario.scenario in {"booking_reservation", "lead_collection", "monitoring_alerts", "qa_regression", "form_filling"}:
            return True
        return detect_domain(goal, "auto") in SCENARIO_ONLY_DOMAINS and scenario.scenario != "research"

    def _build_evidence_summary(
        self,
        observation: Observation,
        plan: Plan,
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

    def _run_scenario(self, goal: str, start_url: str) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        memory = SessionMemory(goal=goal)
        observation = observe(start_url)
        plan: Plan = plan_scenario_goal(goal, observation)
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
                output = execute_action(action, observation)
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
            "agent": self.agent_config.to_dict(),
            "llm": {
                "enabled": self.llm_client.enabled,
                "plan": {
                    "used": False,
                    "mode": "scenario_harness",
                    "evidence_checklist": [],
                },
                "dynamic_agent_loop": {
                    "used": False,
                    "mode": "scenario_harness",
                    "fixed_templates_removed": False,
                    "evidence_checklist": [],
                },
                "report": {"used": False, "reason": "scenario_harness"},
            },
            "goal": goal,
            "start_url": start_url,
            "workflow": {
                "workflow_id": run_id,
                "template": f"{detect_domain(goal, 'auto')}_workflow",
                "goal": goal,
                "domain": detect_domain(goal, 'auto'),
                "summary": plan.summary,
                "nodes": [],
                "confidence": plan.confidence,
                "output_schema": {},
            },
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
            "report": {
                "summary": plan.summary,
                "candidates": [],
                "source_readings": [],
                "recommendations": [],
                "reasoning_outline": [],
                "subquestions": [],
                "search_plan": [],
                "decision_criteria": [],
                "comparison_matrix": [],
                "video_digest": {},
                "multimodal_notes": [],
                "uncertainties": [],
                "next_actions": [],
                "citations": [],
            },
            "ok": ok,
        }
        if self.include_market_comparison:
            result["market_comparison"] = compare_market_profiles(plan.scenario)
        result["metrics"] = summarize_metrics(result)
        return result

    def _run_workflow(self, goal: str, start_url: str, domain: str = "auto") -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        memory = SessionMemory(goal=goal)
        observation = Observation(url=start_url, title="", text="")
        workflow = plan_goal(goal, observation, domain=domain)
        llm_plan = {
            "used": self.llm_client.enabled,
            "mode": "dynamic_agent_loop" if self.llm_client.enabled else "llm_disabled",
            "evidence_checklist": default_search_plan(workflow.domain, workflow.goal),
        }
        dynamic_agent = self.llm_client.enabled
        events: List[Dict[str, Any]] = []
        step_outputs: List[Dict[str, Any]] = []

        try:
            with BrowserSession(headless=self.headless) as session:
                for idx in range(1, self.max_steps + 1):
                    if dynamic_agent:
                        observation = self._attach_planning_visual_summary(goal, observation)
                        decision = plan_next_action(
                            workflow=workflow,
                            observation=observation,
                            memory_dump=memory.dump(),
                            step_outputs=step_outputs,
                            client=self.llm_client,
                            step_id=idx,
                        )
                        if decision.get("ok"):
                            node = decision["node"]
                            node.inputs["multimodal_planning_used"] = bool(decision.get("multimodal_planning_used"))
                            if decision.get("multimodal_planning_error"):
                                node.inputs["multimodal_planning_error"] = decision.get("multimodal_planning_error")
                            if decision.get("status") in {"final", "blocked"} and node.action == "stop":
                                events.append(
                                    make_event(
                                        run_id=run_id,
                                        step_id=idx,
                                        phase="agent_stop",
                                        tool="stop",
                                        payload={
                                            "status": decision.get("status"),
                                            "rationale": decision.get("rationale"),
                                            "checklist_status": decision.get("checklist_status", []),
                                        },
                                        output={"result": {"ok": decision.get("status") == "final"}},
                                        url=observation.url,
                                        start=time(),
                                    ).to_dict()
                                )
                                break
                        else:
                            node = self._fallback_dynamic_node(idx, decision.get("reason", "dynamic_plan_failed"))
                    else:
                        break
                    result, verdict, event_dict = self._execute_with_retries(
                        session=session,
                        run_id=run_id,
                        step_id=idx,
                        node=node,
                        observation=observation,
                    )
                    events.append(event_dict)
                    if dynamic_agent:
                        workflow.nodes.append(node)
                    memory.write_node(node.to_dict(), result.to_dict(), verdict.to_dict())
                    observation = session.observe_current_page(
                        previous=result.to_observation(observation),
                        node_id=f"observe-{idx}",
                        seed_fields=result.fields,
                    )
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
                    if dynamic_agent and decision.get("ok") and decision.get("status") == "final":
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

        result_payload = {
            "run_id": run_id,
            "agent": self.agent_config.to_dict(),
            "llm": {
                "enabled": self.llm_client.enabled,
                "plan": llm_plan,
                "dynamic_agent_loop": {
                    "used": dynamic_agent,
                    "mode": "observe_plan_act_verify" if dynamic_agent else "llm_required",
                    "fixed_templates_removed": True,
                    "evidence_checklist": default_search_plan(workflow.domain, workflow.goal),
                },
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
        result_payload["metrics"] = summarize_metrics(result_payload)
        return result_payload

    def _fallback_dynamic_node(self, step_id: int, reason: str) -> WorkflowNode:
        return WorkflowNode(
            id=f"d{step_id}",
            type="artifact",
            instruction="动态规划失败，抽取当前页面作为安全降级证据",
            action="extract_page",
            inputs={"source": "general", "dynamic_fallback": reason},
            depends_on=[],
            success_criteria=["action_ok", "evidence_or_fields"],
        )

    def _attach_planning_visual_summary(self, goal: str, observation: Observation) -> Observation:
        # The planner already receives the current screenshot directly when
        # available. Avoid a second vision call per turn so extension runs stay
        # responsive in real browser-control scenarios.
        if not self.agent_config.use_visual_precheck:
            return observation
        return observation

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
                    "provider": provider.provider_name,
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
                "provider": provider.provider_name,
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
