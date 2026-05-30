from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from browser_agent.config import AgentConfig


@dataclass
class LLMResponse:
    ok: bool
    content: str = ""
    error: Optional[str] = None
    raw: Dict[str, Any] | None = None


class LLMClient:
    """OpenAI-compatible chat client, configured for DeepSeek by default."""

    def __init__(self, config: AgentConfig, timeout_sec: int = 45) -> None:
        self.config = config
        self.timeout_sec = timeout_sec

    @property
    def enabled(self) -> bool:
        return self.config.use_llm and self.config.api_key_configured

    def chat(self, system: str, user: str, temperature: float = 0.2) -> LLMResponse:
        if not self.enabled:
            return LLMResponse(ok=False, error="llm_disabled_or_api_key_missing")
        endpoint = self.config.api_base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {os.getenv(self.config.api_key_env, '')}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return LLMResponse(ok=False, error=f"http_{exc.code}: {detail[:500]}")
        except Exception as exc:
            return LLMResponse(ok=False, error=str(exc))
        try:
            content = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return LLMResponse(ok=False, error="invalid_llm_response", raw=raw)
        return LLMResponse(ok=True, content=content, raw=raw)

    def chat_json(self, system: str, user: str, temperature: float = 0.1) -> Dict[str, Any]:
        response = self.chat(system, user, temperature=temperature)
        if not response.ok:
            return {"ok": False, "error": response.error}
        parsed = _extract_json(response.content)
        if parsed is None:
            return {"ok": False, "error": "json_parse_failed", "content": response.content}
        parsed.setdefault("ok", True)
        return parsed


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
