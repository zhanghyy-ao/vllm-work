from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Observation:
    url: str
    title: str
    text: str
    elements: List[Dict[str, Any]] = field(default_factory=list)
    screenshot_path: str = ""


@dataclass
class Action:
    tool: str
    reason: str
    target: str = ""
    value: str = ""
    sensitive: bool = False


@dataclass
class Plan:
    summary: str
    actions: List[Action]
    confidence: float = 0.6
    scenario: str = "research"
    risk_level: str = "medium"
    deliverable: str = "summary"
    success_checks: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScenarioDefinition:
    name: str
    summary: str
    confidence: float
    keywords: List[str]
    action_specs: List[Dict[str, str]]
    risk_level: str = "medium"
    deliverable: str = "summary"
    approval_actions: List[str] = field(default_factory=list)
    success_checks: List[str] = field(default_factory=list)


def action_from_spec(spec: Dict[str, str], approval_actions: List[str] | None = None) -> Action:
    approval_actions = approval_actions or []
    return Action(
        tool=spec["tool"],
        reason=spec["reason"],
        target=spec.get("target", ""),
        value=spec.get("value", ""),
        sensitive=spec["tool"] in approval_actions,
    )
