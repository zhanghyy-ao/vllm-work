from __future__ import annotations

from browser_agent.types import Observation


def observe(url: str) -> Observation:
    """Placeholder observer.

    Real implementation should combine DOM + screenshot + OCR + coordinates.
    """
    return Observation(
        url=url,
        title="Stub Page",
        text="This is a stub observation from harness runtime.",
        elements=[
            {"id": "e1", "role": "searchbox", "label": "搜索"},
            {"id": "e2", "role": "button", "label": "搜索按钮"},
        ],
    )
