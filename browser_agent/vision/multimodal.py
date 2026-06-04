from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Dict, List
import requests

from browser_agent.config import AgentConfig


class GeminiVisionProvider:
    """Optional multimodal handoff for screenshots/key frames.

    The current browser workflow can already capture screenshots and video-page
    metadata. This provider is intentionally optional: without a configured key
    it returns a structured unavailable result instead of failing the workflow.

    Supported providers:
    - gemini: Google Generative Language API.
    - openai/openai_compatible: Chat Completions APIs that accept image_url input.
    """

    def __init__(self, config: AgentConfig, timeout_sec: int = 45) -> None:
        self.config = config
        self.timeout_sec = timeout_sec

    @property
    def enabled(self) -> bool:
        return self.config.vision_provider in {"gemini", "openai", "openai_compatible"} and bool(self.config.vision_api_key_value)

    @property
    def provider_name(self) -> str:
        return self.config.vision_provider

    def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "reason": "vision_api_key_missing_or_provider_disabled", "provider": self.config.vision_provider}
        path = Path(image_path)
        if not path.exists():
            return {"ok": False, "reason": "image_not_found", "path": image_path}
        mime_type = _mime_type(path)
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        if self.config.vision_provider in {"openai", "openai_compatible"}:
            return self._analyze_image_openai_compatible(data, mime_type, prompt)
        return self._analyze_image_gemini(data, mime_type, prompt)

    def _analyze_image_gemini(self, data: str, mime_type: str, prompt: str) -> Dict[str, Any]:
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.vision_model}:generateContent"
            f"?key={self.config.vision_api_key_value}"
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
        try:
            response = requests.post(endpoint, json=payload, timeout=self.timeout_sec)
            raw = response.json()
        except requests.RequestException as exc:
            return {"ok": False, "reason": str(exc)}
        except ValueError:
            return {"ok": False, "reason": "invalid_json_response"}
        if not response.ok:
            return {"ok": False, "reason": f"http_{response.status_code}", "detail": response.text[:500]}
        text = _extract_text(raw)
        return {"ok": bool(text), "provider": "gemini", "model": self.config.vision_model, "text": text, "raw": raw}

    def _analyze_image_openai_compatible(self, data: str, mime_type: str, prompt: str) -> Dict[str, Any]:
        endpoint = self.config.vision_api_base_url.rstrip("/") + "/chat/completions"
        models = [self.config.vision_model, *getattr(self.config, "vision_model_fallbacks", [])]
        last_result = {"ok": False, "reason": "vision_model_unavailable"}
        for model_name in _unique_models(models):
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{data}"}},
                        ],
                    }
                ],
                "temperature": 0.1,
            }
            try:
                response = requests.post(
                    endpoint,
                    headers=_request_headers(self.config.vision_api_key_value, self.config.http_user_agent),
                    json=payload,
                    timeout=self.timeout_sec,
                )
            except requests.RequestException as exc:
                return {"ok": False, "reason": str(exc)}
            try:
                raw = response.json()
            except ValueError:
                raw = {}
            if response.ok:
                try:
                    text = raw["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError):
                    text = ""
                return {
                    "ok": bool(text),
                    "provider": self.config.vision_provider,
                    "model": raw.get("model", model_name),
                    "text": text,
                    "raw": raw,
                }
            detail = response.text[:500]
            last_result = {"ok": False, "reason": f"http_{response.status_code}", "detail": detail, "model": model_name}
            if not _is_retryable_model_error(response.status_code, raw, detail):
                break
        return last_result


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


def _request_headers(api_key: str, user_agent: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": user_agent,
    }


def _is_retryable_model_error(status_code: int, raw: Dict[str, Any], detail: str) -> bool:
    error = raw.get("error") if isinstance(raw, dict) else None
    code = str((error or {}).get("code", "")).lower()
    message = str((error or {}).get("message", "") or detail).lower()
    if status_code in {429, 500, 502, 503, 504}:
        return True
    return code in {"model_not_found"} or "no available channel for model" in message


def _unique_models(models: List[str]) -> List[str]:
    ordered: List[str] = []
    seen = set()
    for item in models:
        name = str(item or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return ordered
