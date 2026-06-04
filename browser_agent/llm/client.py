from __future__ import annotations

import json
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from browser_agent.config import AgentConfig


@dataclass
class LLMResponse:
    ok: bool
    content: str = ""
    error: Optional[str] = None
    raw: Dict[str, Any] | None = None


class LLMClient:
    """OpenAI-compatible chat client for text and screenshot-aware planning."""

    def __init__(self, config: AgentConfig, timeout_sec: int = 30) -> None:
        self.config = config
        self.timeout_sec = int(config.llm_timeout_sec or timeout_sec)

    @property
    def enabled(self) -> bool:
        return self.config.use_llm and self.config.api_key_configured

    def chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 1200,
        timeout_sec: Optional[int] = None,
    ) -> LLMResponse:
        if not self.enabled:
            return LLMResponse(ok=False, error="llm_disabled_or_api_key_missing")
        endpoint = self.config.api_base_url.rstrip("/") + "/chat/completions"
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return self._chat_completion(
            endpoint,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_sec=timeout_sec,
        )

    def chat_json(
        self,
        system: str,
        user: str,
        temperature: float = 0.1,
        max_tokens: int = 1200,
        timeout_sec: Optional[int] = None,
    ) -> Dict[str, Any]:
        response = self.chat(system, user, temperature=temperature, max_tokens=max_tokens, timeout_sec=timeout_sec)
        if not response.ok:
            return {"ok": False, "error": response.error}
        parsed = _extract_json(response.content)
        if parsed is None:
            return {"ok": False, "error": "json_parse_failed", "content": response.content}
        parsed.setdefault("ok", True)
        return parsed

    def chat_json_with_image(
        self,
        system: str,
        user: str,
        image_path: str,
        temperature: float = 0.1,
        max_tokens: int = 1200,
        timeout_sec: Optional[int] = None,
    ) -> Dict[str, Any]:
        response = self.chat_with_image(
            system,
            user,
            image_path=image_path,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_sec=timeout_sec,
        )
        if not response.ok:
            return {"ok": False, "error": response.error}
        parsed = _extract_json(response.content)
        if parsed is None:
            return {"ok": False, "error": "json_parse_failed", "content": response.content}
        parsed.setdefault("ok", True)
        return parsed

    def chat_with_image(
        self,
        system: str,
        user: str,
        image_path: str,
        temperature: float = 0.1,
        max_tokens: int = 1200,
        timeout_sec: Optional[int] = None,
    ) -> LLMResponse:
        if not self.enabled:
            return LLMResponse(ok=False, error="llm_disabled_or_api_key_missing")
        path = Path(image_path)
        if not path.exists():
            return LLMResponse(ok=False, error="image_not_found")
        mime_type = _mime_type(path)
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        endpoint = self.config.api_base_url.rstrip("/") + "/chat/completions"
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{data}"}},
                ],
            },
        ]
        return self._chat_completion(
            endpoint,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            models=[self.config.vision_model, *getattr(self.config, "vision_model_fallbacks", [])],
            timeout_sec=timeout_sec,
        )

    def _chat_completion(
        self,
        endpoint: str,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_tokens: int,
        models: Optional[List[str]] = None,
        timeout_sec: Optional[int] = None,
    ) -> LLMResponse:
        last_error = "unknown_error"
        last_raw: Dict[str, Any] | None = None
        request_timeout = timeout_sec or self.timeout_sec
        for model_name in _unique_models(models or [self.config.model, *getattr(self.config, "model_fallbacks", [])]):
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            try:
                response = requests.post(
                    endpoint,
                    headers=_request_headers(self.config.api_key_value, self.config.http_user_agent),
                    json=payload,
                    timeout=(10, request_timeout),
                )
            except requests.RequestException as exc:
                return LLMResponse(ok=False, error=str(exc))
            raw, detail = _response_json_and_text(response)
            if response.ok:
                try:
                    content = raw["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError):
                    return LLMResponse(ok=False, error="invalid_llm_response", raw=raw)
                raw["resolved_model"] = raw.get("model", model_name)
                return LLMResponse(ok=True, content=content, raw=raw)
            last_error = f"http_{response.status_code}: {detail[:500]}"
            last_raw = raw
            if not _is_retryable_model_error(response.status_code, raw, detail):
                break
        return LLMResponse(ok=False, error=last_error, raw=last_raw)


def _extract_json(content: str) -> Dict[str, Any] | None:
    text = content.strip()
    if text.startswith("```"):
        lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None


def _mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "image/png"


def _request_headers(api_key: str, user_agent: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": user_agent,
    }


def _response_json_and_text(response: requests.Response) -> tuple[Dict[str, Any], str]:
    text = response.text
    try:
        raw = response.json()
    except ValueError:
        raw = {}
    return raw, text


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


def compact_evidence(evidence: List[Dict[str, Any]], limit: int = 12) -> List[Dict[str, Any]]:
    compact: List[Dict[str, Any]] = []
    for item in evidence[:limit]:
        compact.append(
            {
                "source_type": item.get("source_type"),
                "source_url": item.get("source_url"),
                "claim": item.get("claim"),
                "support": str(item.get("support", ""))[:500],
                "confidence": item.get("confidence"),
            }
        )
    return compact
