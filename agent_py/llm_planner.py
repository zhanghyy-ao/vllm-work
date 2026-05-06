from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from json import JSONDecodeError
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import quote

from .config import load_dotenv
from .schema import Observation, Plan
from .safety import sanitize_plan, valid_action_types


@dataclass
class LLMConfig:
    api_base: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = ""
    temperature: float = 0.1
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "LLMConfig":
        load_dotenv()
        return cls(
            api_base=os.getenv("BROWSER_AGENT_API_BASE", "https://synai996.space/v1"),
            api_key=os.getenv("BROWSER_AGENT_API_KEY", ""),
            model=os.getenv("BROWSER_AGENT_MODEL", "gemini-3.1-pro-low"),
        )

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.model)


def plan_with_llm(task: str, observation: Observation, config: LLMConfig, allow_explicit_submit: bool = False) -> Plan:
    if not config.enabled:
        raise ValueError("LLM config is incomplete; api_key and model are required.")

    if _use_gemini_native_api(config):
        content = _call_gemini(task, observation, config)
        plan = parse_plan(content)
        return sanitize_plan(plan, observation, allow_explicit_submit=allow_explicit_submit)

    payload = {
        "model": config.model,
        "temperature": config.temperature,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task": task,
                        "observation": compact_observation(observation),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        ],
    }
    data = _post_json(f"{config.api_base.rstrip('/')}/chat/completions", payload, config)
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    plan = parse_plan(content)
    return sanitize_plan(plan, observation, allow_explicit_submit=allow_explicit_submit)


def _use_gemini_native_api(config: LLMConfig) -> bool:
    base = config.api_base.rstrip("/").lower()
    return (
        base.endswith("/gemini")
        or base.endswith("/v1beta")
        or "generativelanguage.googleapis.com" in base
    )


def _call_gemini(task: str, observation: Observation, config: LLMConfig) -> str:
    prompt = "\n\n".join(
        [
            build_system_prompt(),
            json.dumps(
                {
                    "task": task,
                    "observation": compact_observation(observation),
                },
                ensure_ascii=False,
                indent=2,
            ),
        ]
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": config.temperature,
        },
    }
    base = config.api_base.rstrip("/")
    url = f"{base}/v1beta/models/{quote(config.model, safe='')}:generateContent?key={quote(config.api_key, safe='')}"
    data = _post_json(url, payload, config, include_auth=False)
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return "\n".join(part.get("text", "") for part in parts if isinstance(part, dict))


def build_system_prompt() -> str:
    return "\n".join(
        [
            "你是一个安全的 Python 浏览器 Agent Planner。",
            "你只能输出 JSON，不要输出 Markdown 或额外解释。",
            "JSON 格式必须是：{\"summary\": str, \"confidence\": number, \"warnings\": list[str], \"actions\": list[Action]}。",
            f"允许动作类型：{', '.join(valid_action_types())}。",
            "Action 字段：type, targetId, value, key, reason。",
            "targetId 必须来自 observation.elements；不确定时用 extract/summarize/brief/find，而不是猜 targetId。",
            "优先选择 visible=true 且 enabled=true 的元素；填写表单时必须参考 formId/sectionLabel，不要跨表单匹配字段。",
            "点击链接时优先 exact text/label/href 匹配，不能只凭少量字符相似就选择目标。",
            "搜索、打开链接、填写、回复、比较、分析等任务必须包含最终 extract/summarize/brief/collect/find/copy 之一，保证有结果产物。",
            "禁止自动完成发送、提交、付款、删除、发布、上传、下单等最终确认动作；遇到这些只允许 highlight 并写 warning。",
            "优先短计划，通常 1 到 5 步；每步必须有 reason。",
        ]
    )


def compact_observation(observation: Observation) -> Dict[str, Any]:
    return {
        "url": observation.url,
        "title": observation.title,
        "text": observation.text[:3000],
        "headings": observation.headings[:12],
        "links": observation.links[:20],
        "cards": observation.cards[:12],
        "elements": [
            {
                "id": element.id,
                "tag": element.tag,
                "role": element.role,
                "type": element.type,
                "name": element.name,
                "label": element.label,
                "text": element.text,
                "placeholder": element.placeholder,
                "href": element.href,
                "value": element.value,
                "formId": element.form_id,
                "sectionLabel": element.section_label,
                "visible": element.visible,
                "enabled": element.enabled,
                "selector": element.selector,
            }
            for element in observation.elements[:100]
        ],
    }


def parse_plan(content: str) -> Plan:
    text = content.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("LLM did not return a JSON object.")
    data = json.loads(text[start : end + 1])
    return Plan.from_dict(data)


def _post_json(url: str, payload: Dict[str, Any], config: LLMConfig, include_auth: bool = True) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "OpenAI/Python 1.0 browser-agent-demo",
    }
    if include_auth:
        headers["Authorization"] = f"Bearer {config.api_key}"
    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.timeout) as response:
            text = response.read().decode("utf-8", errors="replace")
            try:
                return json.loads(text)
            except JSONDecodeError as exc:
                content_type = response.headers.get("Content-Type", "")
                snippet = text[:240].replace("\n", " ").strip()
                raise RuntimeError(
                    f"LLM response was not JSON. content-type={content_type!r}, body starts with: {snippet!r}"
                ) from exc
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if not detail:
            detail = "<empty response body>"
        raise RuntimeError(f"LLM request failed with HTTP {exc.code}: {detail}") from exc


def try_plan_with_llm(
    task: str,
    observation: Observation,
    config: Optional[LLMConfig],
    allow_explicit_submit: bool = False,
) -> Optional[Plan]:
    if not config or not config.enabled:
        return None
    return plan_with_llm(task, observation, config, allow_explicit_submit=allow_explicit_submit)
