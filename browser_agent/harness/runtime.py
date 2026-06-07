from __future__ import annotations

import uuid
from dataclasses import replace
from time import time
from typing import Any, Dict, List

from browser_agent.agents import build_report_payload, plan_next_step
from browser_agent.browser.action import BrowserSession, execute_action
from browser_agent.browser.observer import observe
from browser_agent.config import AgentConfig, build_agent_config
from browser_agent.evaluation.metrics import summarize_metrics
from browser_agent.failure_policy import classify_failure_type, summarize_failure_types
from browser_agent.harness.events import make_event
from browser_agent.harness.tool_dispatch import dispatch_node
from browser_agent.llm.client import LLMClient
from browser_agent.market.compare import compare_market_profiles
from browser_agent.memory.session import SessionMemory
from browser_agent.planner.tot import detect_domain, plan_goal, plan_scenario_goal
from browser_agent.strategy.research_patterns import default_evidence_plan, requirement_slots
from browser_agent.types import ActionResult, DynamicLoopState, HarnessStepRecord, Observation, Plan, WorkflowNode
from browser_agent.verifier.critic import verify_node, verify_step
from browser_agent.vision.keyframes import visual_inputs_from_video_digest
from browser_agent.vision.multimodal import GeminiVisionProvider, build_video_visual_prompt


SCENARIO_ONLY_DOMAINS = {"form", "booking", "lead", "monitoring", "qa"}


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

    def run(
        self,
        goal: str,
        start_url: str,
        domain: str = "auto",
        initial_observation: Observation | None = None,
    ) -> Dict[str, Any]:
        if self._should_use_scenario_harness(goal, domain):
            return self._run_scenario(goal, start_url)
        if initial_observation is None:
            return self._run_workflow(goal, start_url, domain=domain)
        return self._run_workflow(goal, start_url, domain=domain, initial_observation=initial_observation)

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
        step_outputs: List[HarnessStepRecord] = []
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
                HarnessStepRecord(
                    action=action.tool,
                    ok=verdict["ok"],
                    sensitive=action.sensitive,
                    failure_type=classify_failure_type(
                        ok=verdict["ok"],
                        action=action.tool,
                        detail=output,
                    ),
                    detail=output,
                    reason=verdict["reason"],
                )
            )
            if not verdict["ok"]:
                break

        ok = all(step.ok for step in step_outputs) if step_outputs else False
        evidence = self._build_evidence_summary(observation, plan, [step.to_dict() for step in step_outputs])
        dynamic_loop_state = DynamicLoopState(
            used=False,
            mode="scenario_harness",
            fixed_templates_removed=False,
            evidence_checklist=[],
            requirement_slots=[],
        )
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
                    **dynamic_loop_state.to_dict(),
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
            "steps": [step.to_dict() for step in step_outputs],
            "memory": memory.dump(),
            "events": events,
            "approval_requests": approval_requests,
            "evidence": evidence,
            "failure_analysis": summarize_failure_types([step.to_dict() for step in step_outputs]),
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

    def _run_workflow(
        self,
        goal: str,
        start_url: str,
        domain: str = "auto",
        initial_observation: Observation | None = None,
    ) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        memory = SessionMemory(goal=goal)
        observation = initial_observation or Observation(url=start_url, title="", text="")
        workflow = plan_goal(goal, observation, domain=domain)
        llm_plan = {
            "used": self.llm_client.enabled,
            "mode": "supervisor_navigator_loop" if self.llm_client.enabled else "llm_disabled",
            "evidence_checklist": default_evidence_plan(workflow.domain, workflow.goal),
            "requirement_slots": requirement_slots(workflow.domain, workflow.goal),
        }
        dynamic_agent = self.llm_client.enabled
        events: List[Dict[str, Any]] = []
        step_outputs: List[HarnessStepRecord] = []

        try:
            with BrowserSession(headless=self.headless) as session:
                if initial_observation is None:
                    initial_node = WorkflowNode(
                        id="d0",
                        type="agent_bootstrap",
                        instruction="打开起始页面并采集初始页面状态",
                        action="goto",
                        inputs={"url": start_url, "source": workflow.domain, "bootstrap": True},
                        depends_on=[],
                        success_criteria=["action_ok"],
                    )
                    initial_result = dispatch_node(session, initial_node, observation)
                    initial_verdict = verify_node(initial_node, initial_result, observation)
                    events.append(
                        make_event(
                            run_id=run_id,
                            step_id=0,
                            phase="bootstrap_open",
                            tool="goto",
                            payload={"node": initial_node.to_dict()},
                            output={"result": initial_result.to_dict(), "verdict": initial_verdict.to_dict()},
                            url=initial_result.url or start_url,
                            start=time(),
                        ).to_dict()
                    )
                    memory.write_node(initial_node.to_dict(), initial_result.to_dict(), initial_verdict.to_dict())
                    observation = session.observe_current_page(
                        previous=initial_result.to_observation(observation),
                        node_id="observe-0",
                        seed_fields=initial_result.fields,
                    )
                    if not initial_verdict.ok:
                        step_outputs.append(
                            HarnessStepRecord(
                                node_id=initial_node.id,
                                action=initial_node.action,
                                agent="bootstrap",
                                navigator_agent="bootstrap",
                                ok=initial_verdict.ok,
                                score=initial_verdict.score,
                                fallback_used=initial_result.fallback_used,
                                failure_type=classify_failure_type(
                                    ok=initial_verdict.ok,
                                    action=initial_node.action,
                                    detail=initial_result.to_dict(),
                                    fallback_used=initial_result.fallback_used,
                                ),
                                supervisor_state={},
                                detail=initial_result.to_dict(),
                            )
                        )
                        raise RuntimeError(initial_result.error or "bootstrap_open_failed")
                else:
                    session.sync_to_observation(observation)
                    events.append(
                        make_event(
                            run_id=run_id,
                            step_id=0,
                            phase="bootstrap_resume",
                            tool="observe",
                            payload={"resume_from_current_page": True, "url": observation.url},
                            output={"result": observation.to_dict(), "verdict": {"ok": True, "score": 1.0}},
                            url=observation.url,
                            start=time(),
                        ).to_dict()
                    )
                for idx in range(1, self.max_steps + 1):
                    if dynamic_agent:
                        observation = self._attach_planning_visual_summary(goal, observation)
                        decision = plan_next_step(
                            workflow=workflow,
                            observation=observation,
                            memory_dump=memory.dump(),
                            step_outputs=[step.to_dict() for step in step_outputs],
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
                        HarnessStepRecord(
                            node_id=node.id,
                            action=node.action,
                            agent=decision.get("agent", "supervisor"),
                            navigator_agent=decision.get("navigator_agent", "navigator"),
                            ok=verdict.ok,
                            score=verdict.score,
                            fallback_used=result.fallback_used,
                            failure_type=classify_failure_type(
                                ok=verdict.ok,
                                action=node.action,
                                detail=result.to_dict(),
                                fallback_used=result.fallback_used,
                                planning_reason=node.inputs.get("dynamic_fallback"),
                            ),
                            supervisor_state=decision.get("supervisor_state", {}),
                            detail=result.to_dict(),
                        )
                    )
                    if not verdict.ok and not result.fallback_used:
                        break
                    if dynamic_agent and decision.get("ok") and decision.get("status") == "final":
                        break
        except Exception as exc:
            failure = ActionResult(ok=False, action="browser_session", url=start_url, error=str(exc), human_review_required=True)
            step_outputs.append(
                HarnessStepRecord(
                    action="browser_session",
                    ok=False,
                    failure_type=classify_failure_type(
                        ok=False,
                        action="browser_session",
                        detail=failure.to_dict(),
                    ),
                    detail=failure.to_dict(),
                )
            )

        memory_dump = memory.dump()
        serialized_steps = [step.to_dict() for step in step_outputs]
        artifact, llm_report = build_report_payload(workflow, memory_dump, serialized_steps, self.llm_client)
        self._attach_multimodal_analysis(workflow.goal, artifact)
        ok = bool(step_outputs) and all(step.ok for step in step_outputs)
        dynamic_loop_state = DynamicLoopState(
            used=dynamic_agent,
            mode="supervisor_navigator_verify" if dynamic_agent else "llm_required",
            fixed_templates_removed=True,
            evidence_checklist=default_evidence_plan(workflow.domain, workflow.goal),
            requirement_slots=requirement_slots(workflow.domain, workflow.goal),
        )

        result_payload = {
            "run_id": run_id,
            "agent": self.agent_config.to_dict(),
            "llm": {
                "enabled": self.llm_client.enabled,
                "plan": llm_plan,
                "subagents": {
                    "supervisor": {"used": dynamic_agent, "role": "loop_orchestration"},
                    "navigator": {"used": dynamic_agent, "role": "safe_browser_action_selection"},
                    "verifier": {"used": True, "role": "step_validation_and_retry_hints"},
                    "reporter": {"used": True, "role": "artifact_synthesis"},
                },
                "dynamic_agent_loop": {
                    **dynamic_loop_state.to_dict(),
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
            "steps": serialized_steps,
            "memory": memory_dump,
            "report": artifact.to_dict(),
            "events": events,
            "failure_analysis": summarize_failure_types(serialized_steps),
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
        return replace(node, inputs={**inputs, "fallback_used": fallback})
