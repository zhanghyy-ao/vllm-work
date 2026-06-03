from __future__ import annotations

from browser_agent.types import Observation


def observe(url: str) -> Observation:
    """Harness-safe observation placeholder."""
    return Observation(
        url=url,
        title="Stub Page",
        text=(
            "This is a stub observation from harness runtime. "
            "It simulates DOM, OCR and screenshot metadata for testing."
        ),
        elements=[
            {"id": "search", "role": "searchbox", "label": "搜索"},
            {"id": "submit", "role": "button", "label": "提交"},
            {"id": "compare", "role": "button", "label": "比较"},
            {"id": "booking", "role": "button", "label": "立即预订"},
            {"id": "alerts", "role": "toggle", "label": "开启提醒"},
            {"id": "qa", "role": "button", "label": "运行检查"},
        ],
    )
