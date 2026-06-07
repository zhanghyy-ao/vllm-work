from __future__ import annotations

import json
from typing import Any, Dict, List

from browser_agent.agents.navigator import build_agent_step_context, contextual_evidence_checklist, plan_browser_action
from browser_agent.agents.prompt_loader import load_prompt
from browser_agent.llm.client import compact_evidence, LLMClient
from browser_agent.strategy.research_patterns import requirement_slots
from browser_agent.types import Observation, SupervisorState, WorkflowSpec


def summarize_supervisor_state(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
) -> SupervisorState:
    context = build_agent_step_context(workflow, observation, memory_dump, step_outputs, step_id=len(step_outputs) + 1)
    slot_checklist = [
        {
            "requirement_slot": item.get("slot"),
            "purpose": item.get("purpose"),
            "source": item.get("source"),
        }
        for item in requirement_slots(workflow.domain, workflow.goal)
    ]
    return SupervisorState(
        goal=workflow.goal,
        domain=workflow.domain,
        current_url=observation.url,
        current_title=observation.title,
        candidate_count=len(observation.elements or []),
        recent_actions=[item.get("action") for item in context.memory.get("recent_traces", [])[:5]],
        evidence_count=len(context.memory.get("evidence", [])),
        evidence_sample=context.memory.get("evidence", [])[:5],
        page_fingerprint=context.page_fingerprint.to_dict(),
        page_capabilities=context.current_page_capabilities,
        priority_requirement_slot=context.priority_requirement_slot,
        checklist=context.evidence_checklist,
        requirement_checklist=slot_checklist,
        completed_step_count=len(step_outputs),
    )


def build_supervisor_prompt_payload(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
    step_id: int,
) -> str:
    payload = {
        "goal": workflow.goal,
        "domain": workflow.domain,
        "step_id": step_id,
        "current_page": {
            "url": observation.url,
            "title": observation.title,
            "text_excerpt": str(observation.text or "")[:1200],
            "visual_summary": observation.visual_summary,
            "candidate_count": len(observation.elements or []),
        },
        "supervisor_state": summarize_supervisor_state(
            workflow=workflow,
            observation=observation,
            memory_dump=memory_dump,
            step_outputs=step_outputs,
        ).to_dict(),
    }
    return json.dumps(payload, ensure_ascii=False)


def plan_next_step(
    workflow: WorkflowSpec,
    observation: Observation,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
    client: LLMClient | None,
    step_id: int,
) -> Dict[str, Any]:
    """Supervisor agent.

    In this version the supervisor owns loop-level state summarization and
    prompt separation. Concrete browser action choice is still delegated to the
    navigator agent.
    """
    supervisor_state = summarize_supervisor_state(
        workflow=workflow,
        observation=observation,
        memory_dump=memory_dump,
        step_outputs=step_outputs,
    )
    decision = plan_browser_action(
        workflow=workflow,
        observation=observation,
        memory_dump=memory_dump,
        step_outputs=step_outputs,
        client=client,
        step_id=step_id,
    )
    navigator_agent = decision.get("agent", "navigator")
    decision["agent"] = "supervisor"
    decision["navigator_agent"] = navigator_agent
    decision["supervisor_prompt"] = {
        "system": load_prompt("supervisor_system.md"),
        "user": build_supervisor_prompt_payload(
            workflow=workflow,
            observation=observation,
            memory_dump=memory_dump,
            step_outputs=step_outputs,
            step_id=step_id,
        ),
    }
    decision["supervisor_state"] = supervisor_state.to_dict()
    return decision
