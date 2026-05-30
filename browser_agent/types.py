from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Observation:
    url: str
    title: str
    text: str
    elements: List[Dict[str, Any]] = field(default_factory=list)
    screenshot_path: str = ""
    extracted_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Action:
    tool: str
    reason: str
    target: str = ""
    value: str = ""


@dataclass
class Plan:
    summary: str
    actions: List[Action]
    confidence: float = 0.6


@dataclass
class WorkflowNode:
    id: str
    type: str
    instruction: str
    action: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {"max_retries": 2})

    def to_action(self) -> Action:
        return Action(
            tool=self.action,
            reason=self.instruction,
            target=str(self.inputs.get("target", "")),
            value=str(self.inputs.get("query", self.inputs.get("url", self.inputs.get("value", "")))),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowSpec:
    workflow_id: str
    template: str
    goal: str
    domain: str
    summary: str
    nodes: List[WorkflowNode]
    confidence: float = 0.7
    output_schema: Dict[str, Any] = field(default_factory=dict)

    def to_plan(self) -> Plan:
        return Plan(
            summary=self.summary,
            actions=[node.to_action() for node in self.nodes],
            confidence=self.confidence,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceItem:
    evidence_id: str
    source_type: str
    source_url: str
    claim: str
    support: str
    confidence: float = 0.6
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ActionResult:
    ok: bool
    action: str
    url: str = ""
    title: str = ""
    text: str = ""
    fields: Dict[str, Any] = field(default_factory=dict)
    evidence: List[EvidenceItem] = field(default_factory=list)
    error: Optional[str] = None
    fallback_used: Optional[str] = None
    human_review_required: bool = False

    def to_observation(self, previous: Observation) -> Observation:
        next_elements = list(previous.elements)
        if isinstance(self.fields.get("links"), list):
            seen = {
                str(item.get("href") or item.get("url") or "")
                for item in next_elements
                if isinstance(item, dict)
            }
            for item in self.fields["links"]:
                if not isinstance(item, dict):
                    continue
                key = str(item.get("href") or item.get("url") or "")
                if not key or key in seen:
                    continue
                seen.add(key)
                next_elements.append(item)
        return Observation(
            url=self.url or previous.url,
            title=self.title or previous.title,
            text=self.text or previous.text,
            elements=next_elements,
            screenshot_path=str(self.fields.get("screenshot_path", previous.screenshot_path)),
            extracted_fields=self.fields,
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["evidence"] = [item.to_dict() for item in self.evidence]
        return data


@dataclass
class VerificationResult:
    ok: bool
    score: float
    checks: List[Dict[str, Any]]
    retry_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StructuredArtifact:
    summary: str
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    source_readings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_outline: List[str] = field(default_factory=list)
    subquestions: List[str] = field(default_factory=list)
    search_plan: List[Dict[str, Any]] = field(default_factory=list)
    decision_criteria: List[Dict[str, Any]] = field(default_factory=list)
    comparison_matrix: List[Dict[str, Any]] = field(default_factory=list)
    video_digest: Dict[str, Any] = field(default_factory=dict)
    multimodal_notes: List[Dict[str, Any]] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
