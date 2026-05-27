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


@dataclass
class Plan:
    summary: str
    actions: List[Action]
    confidence: float = 0.6

