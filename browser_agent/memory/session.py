from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from browser_agent.types import EvidenceItem


@dataclass
class SessionMemory:
    goal: str
    traces: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)

    def write(self, tool: str, output: Dict[str, Any], verdict: Dict[str, Any]) -> None:
        self.traces.append({"tool": tool, "output": output, "verdict": verdict})
        for item in output.get("evidence", []):
            if isinstance(item, EvidenceItem):
                self.evidence.append(item)
            elif isinstance(item, dict):
                self.evidence.append(EvidenceItem(**item))

    def write_node(self, node: Dict[str, Any], output: Dict[str, Any], verdict: Dict[str, Any]) -> None:
        self.traces.append({"node": node, "output": output, "verdict": verdict})
        for item in output.get("evidence", []):
            if isinstance(item, EvidenceItem):
                self.evidence.append(item)
            elif isinstance(item, dict):
                self.evidence.append(EvidenceItem(**item))

    def dump(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "traces": self.traces,
            "evidence": [item.to_dict() for item in self.evidence],
        }
