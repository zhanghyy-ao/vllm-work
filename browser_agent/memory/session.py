from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SessionMemory:
    goal: str
    traces: List[Dict[str, Any]] = field(default_factory=list)

    def write(self, tool: str, output: Dict[str, Any], verdict: Dict[str, Any]) -> None:
        self.traces.append({"tool": tool, "output": output, "verdict": verdict})

    def dump(self) -> Dict[str, Any]:
        return {"goal": self.goal, "traces": self.traces}
