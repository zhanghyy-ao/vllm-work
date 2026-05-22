from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Element:
    """Normalized interactive element descriptor shared by planners and executors."""
    id: str
    tag: str
    selector: str = ""
    role: str = ""
    type: str = ""
    name: str = ""
    label: str = ""
    text: str = ""
    placeholder: str = ""
    href: str = ""
    value: str = ""
    form_id: str = ""
    section_label: str = ""
    visible: bool = True
    enabled: bool = True
    bbox: Dict[str, float] = field(default_factory=dict)
    content_editable: bool = False
    clickable: bool = False

    def haystack(self) -> str:
        return " ".join(
            part
            for part in [
                self.id,
                self.selector,
                self.tag,
                self.role,
                self.type,
                self.name,
                self.label,
                self.text,
                self.placeholder,
                self.href,
                self.value,
                self.form_id,
                self.section_label,
            ]
            if part
        ).lower()


@dataclass
class Observation:
    """Snapshot of current page state used as agent perception input."""
    url: str
    title: str
    text: str
    elements: List[Element]
    cards: List[Dict[str, str]] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    prices: List[str] = field(default_factory=list)
    headings: List[str] = field(default_factory=list)
    screenshot_path: str = ""
    viewport: Dict[str, int] = field(default_factory=dict)


@dataclass
class Action:
    """Atomic action requested by planner and consumed by executors."""
    type: str
    target_id: Optional[str] = None
    value: Any = None
    key: Optional[str] = None
    reason: str = ""
    risk_level: str = "low"
    requires_confirmation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = {"type": self.type, "reason": self.reason}
        if self.target_id:
            data["targetId"] = self.target_id
        if self.value is not None:
            data["value"] = self.value
        if self.key:
            data["key"] = self.key
        if self.risk_level != "low":
            data["riskLevel"] = self.risk_level
        if self.requires_confirmation:
            data["requiresConfirmation"] = self.requires_confirmation
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        return cls(
            type=str(data.get("type", "")),
            target_id=data.get("targetId") or data.get("target_id"),
            value=data.get("value"),
            key=data.get("key"),
            reason=str(data.get("reason", "")),
            risk_level=str(data.get("riskLevel") or data.get("risk_level") or "low"),
            requires_confirmation=bool(data.get("requiresConfirmation") or data.get("requires_confirmation")),
        )


@dataclass
class Plan:
    """Planner output: summary, confidence, warnings, ordered action list."""
    summary: str
    confidence: float
    actions: List[Action]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "confidence": self.confidence,
            "warnings": self.warnings,
            "actions": [action.to_dict() for action in self.actions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Plan":
        actions = data.get("actions") if isinstance(data, dict) else []
        return cls(
            summary=str(data.get("summary", "LLM 生成计划")),
            confidence=float(data.get("confidence", 0.5) or 0.5),
            warnings=[str(item) for item in data.get("warnings", [])] if isinstance(data.get("warnings", []), list) else [],
            actions=[Action.from_dict(item) for item in actions if isinstance(item, dict)],
        )


@dataclass
class ActionResult:
    """Execution status for one action."""
    action: Action
    ok: bool
    output: Any = None
    error: str = ""
    url: str = ""
    artifact: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.to_dict(),
            "ok": self.ok,
            "output": self.output,
            "error": self.error,
            "url": self.url,
            "artifact": self.artifact,
        }


@dataclass
class ExecutionResult:
    """Aggregated execution logs and artifact for a run or round."""
    url: str
    logs: List[ActionResult]
    artifact: str = ""
    trajectory: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(item.ok for item in self.logs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "url": self.url,
            "artifact": self.artifact,
            "logs": [item.to_dict() for item in self.logs],
            "trajectory": self.trajectory,
        }
