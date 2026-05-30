from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from browser_agent.config import AgentConfig


class GeminiVisionProvider:
    """Minimal Gemini multimodal handoff for screenshots/key frames.

    The current browser workflow can already capture screenshots and video-page
    metadata. This provider is intentionally optional: without GEMINI_API_KEY it
    returns a structured unavailable result instead of failing the workflow.
    """

    def __init__(self, config: AgentConfig, timeout_sec: int = 45) -> None:
        self.config = config
        self.timeout_sec = timeout_sec

    @property
    def enabled(self) -> bool:
        return self.config.vision_provider == "gemini" and bool(os.getenv(self.config.vision_api_key_env))

    def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "reason": "gemini_api_key_missing_or_provider_disabled", "provider": self.config.vision_provider}
        path = Path(image_path)
        if not path.exists():
            return {"ok": False, "reason": "image_not_found", "path": image_path}
        mime_type = _mime_type(path)
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.vision_model}:generateContent"
            f"?key={os.getenv(self.config.vision_api_key_env, '')}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": mime_type, "data": data}},
                    ]
                }
            ]
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return {"ok": False, "reason": f"http_{exc.code}", "detail": exc.read().decode("utf-8", errors="replace")[:500]}
        except Exception as exc:
            return {"ok": False, "reason": str(exc)}
        text = _extract_text(raw)
        return {"ok": bool(text), "provider": "gemini", "model": self.config.vision_model, "text": text, "raw": raw}


def build_video_visual_prompt(goal: str, known_context: str = "") -> str:
    return (
        "你是视频内容理解助手。请根据截图/关键帧识别画面中的主题、演示步骤、重要文字、UI状态和可能的时间线线索。"
        "不要编造未出现的信息；如果画面不足以判断，请明确说明。\n"
        f"用户任务：{goal}\n"
        f"已知上下文：{known_context[:1200]}"
    )


def _mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "image/png"


def _extract_text(raw: Dict[str, Any]) -> str:
    parts: List[str] = []
    for candidate in raw.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            if isinstance(part.get("text"), str):
                parts.append(part["text"])
    return "\n".join(parts).strip()
