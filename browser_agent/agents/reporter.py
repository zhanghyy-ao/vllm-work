from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from browser_agent.agents.prompt_loader import load_prompt
from browser_agent.llm.agent import build_llm_report
from browser_agent.llm.client import LLMClient
from browser_agent.output.report_builder import build_report
from browser_agent.types import StructuredArtifact, WorkflowSpec


def build_report_payload(
    workflow: WorkflowSpec,
    memory_dump: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
    client: LLMClient,
) -> Tuple[StructuredArtifact, Dict[str, Any]]:
    """Reporter agent.

    Builds a deterministic structured artifact first, then optionally lets the
    LLM enhance the final summary and recommendation-oriented fields.
    """
    artifact = build_report(workflow, memory_dump, step_outputs)
    llm_report = build_llm_report(workflow, memory_dump, client)
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
        if isinstance(report_payload.get("requirement_progression"), list) and report_payload["requirement_progression"]:
            artifact.requirement_progression = report_payload["requirement_progression"]
        if isinstance(report_payload.get("evidence_plan"), list) and report_payload["evidence_plan"]:
            artifact.evidence_plan = report_payload["evidence_plan"]
        if (
            isinstance(report_payload.get("search_plan"), list)
            and report_payload["search_plan"]
            and not artifact.requirement_progression
            and not artifact.evidence_plan
        ):
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
    llm_report["agent"] = "reporter"
    llm_report["prompt"] = {
        "system": load_prompt("reporter_system.md"),
        "user": json.dumps(
            {
                "goal": workflow.goal,
                "domain": workflow.domain,
                "step_count": len(step_outputs),
                "evidence_count": len(memory_dump.get("evidence", [])) if isinstance(memory_dump, dict) else 0,
            },
            ensure_ascii=False,
        ),
    }
    return artifact, llm_report
