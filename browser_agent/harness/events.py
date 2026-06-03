from __future__ import annotations

from dataclasses import asdict, dataclass
from time import time
from typing import Any, Dict


@dataclass
class HarnessEvent:
    run_id: str
    step_id: int
    phase: str
    tool: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    latency_ms: int
    url: str
    ts: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def make_event(
    run_id: str,
    step_id: int,
    phase: str,
    tool: str,
    payload: Dict[str, Any],
    output: Dict[str, Any],
    url: str,
    start: float,
) -> HarnessEvent:
    return HarnessEvent(
        run_id=run_id,
        step_id=step_id,
        phase=phase,
        tool=tool,
        input=payload,
        output=output,
        latency_ms=int((time() - start) * 1000),
        url=url,
        ts=time(),
    )
