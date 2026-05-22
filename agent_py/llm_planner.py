from __future__ import annotations

import json
import os
from json import JSONDecodeError
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from .config import load_dotenv
from .schema import Observation, Plan
from .safety import sanitize_plan, valid_action_types


@dataclass
class LLMConfig:
    """Runtime LLM configuration loaded from .env or request overrides."""
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

    @property
    def transport(self) -> str:
        return infer_transport(self)


def plan_with_llm(task: str, observation: Observation, config: LLMConfig, allow_explicit_submit: bool = False) -> Plan:
    """Build a plan via LLM and run it through safety sanitization."""
    if not config.enabled:
        raise ValueError("LLM config is incomplete; api_key and model are required.")
    content = request_text_completion(
        [
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
        config,
    )
    plan = parse_plan(content)
    return sanitize_plan(plan, observation, allow_explicit_submit=allow_explicit_submit)


def infer_transport(config: LLMConfig) -> str:
    if _use_gemini_native_api(config):
        return "gemini-native"
    return "openai-chat"


def _use_gemini_native_api(config: LLMConfig) -> bool:
    base = config.api_base.rstrip("/").lower()
    if _is_gemini_model(config.model) and "synai996.space" in base:
        return True
    return (
        base.endswith("/gemini")
        or base.endswith("/v1beta")
        or "generativelanguage.googleapis.com" in base
    )


def request_text_completion(messages: List[Dict[str, str]], config: LLMConfig, temperature: Optional[float] = None) -> str:
    """Unified text generation entry for OpenAI-compatible and Gemini-native transports."""
    if _use_gemini_native_api(config):
        return _call_gemini_messages(messages, config, temperature=temperature)
    payload = {
        "model": config.model,
        "temperature": config.temperature if temperature is None else temperature,
        "messages": messages,
    }
    data = _post_json(f"{config.api_base.rstrip('/')}/chat/completions", payload, config)
    return str(data.get("choices", [{}])[0].get("message", {}).get("content", ""))


def _call_gemini_messages(messages: List[Dict[str, str]], config: LLMConfig, temperature: Optional[float] = None) -> str:
    """Send prompt to Gemini generateContent API and return plain text response."""
    prompt = _messages_to_gemini_prompt(messages)
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": config.temperature if temperature is None else temperature,
        },
    }
    url = _primary_gemini_url(config)
    data = _post_json(url, payload, config, include_auth=False)
    if _looks_like_html_response(data):
        raise RuntimeError("Gemini endpoint returned HTML instead of JSON.")
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if text:
        return text
    raise RuntimeError("Gemini endpoint returned empty text.")


def _primary_gemini_url(config: LLMConfig) -> str:
    base = config.api_base.rstrip("/")
    root = base
    if base.endswith("/v1"):
        root = base[:-3]
    if root.endswith("/gemini"):
        root = root[: -len("/gemini")]
    model = quote(config.model, safe="")
    key = quote(config.api_key, safe="")
    return f"{root}/v1beta/models/{model}:generateContent?key={key}"


def _messages_to_gemini_prompt(messages: List[Dict[str, str]]) -> str:
    chunks = []
    for message in messages:
        role = str(message.get("role") or "user").upper()
        content = str(message.get("content") or "").strip()
        if content:
            chunks.append(f"[{role}]\n{content}")
    return "\n\n".join(chunks)


def _is_gemini_model(model: str) -> bool:
    return str(model or "").strip().lower().startswith("gemini-")


def _looks_like_html_response(data: Dict[str, Any]) -> bool:
    if not data:
        return False
    if "candidates" in data or "error" in data:
        return False
    text = json.dumps(data, ensure_ascii=False)[:120].lower()
    return "<!doctype html" in text or "<html" in text


def _explain_synai_error(exc: Exception) -> str:
    message = str(exc)
    lowered = message.lower()
    if "eof occurred in violation of protocol" in lowered:
        return "Synai TLS 连接被异常中断，通常是第三方网关不稳定或临时限流。"
    if "max retries exceeded" in lowered:
        return "多次重试后仍未连通 Synai，请稍后重试。"
    if "read timed out" in lowered or "timeout" in lowered:
        return "Synai 请求超时，通常表示第三方模型通道响应过慢。"
    if "429" in lowered:
        return "Synai 返回 429，当前请求过快或上游正在限流。"
    if "503" in lowered:
        return "Synai 返回 503，当前模型通道暂时不可用。"
    if "service has been disabled in this account" in lowered:
        return "Synai 返回 403：当前账号对 OpenAI 兼容服务已被禁用。"
    if "auth_unavailable" in lowered:
        return "Synai 当前没有为该模型提供可用上游鉴权/provider。"
    if "invalid_grant" in lowered:
        return "Synai 拒绝了当前 Gemini 鉴权，通常表示该 key 对 Gemini 接口无效或网关未开通。"
    if "returned html instead of json" in lowered:
        return "请求命中了 Synai 的网页入口而不是可用的 Gemini JSON 接口。"
    return message


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
    """HTTP JSON helper with retry and consistent error normalization."""
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
    except ImportError as exc:
        raise RuntimeError("requests is not installed. Run: python3 -m pip install -r requirements.txt") from exc

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Connection": "close",
        "User-Agent": "OpenAI/Python 1.0 browser-agent-demo",
    }
    if include_auth:
        headers["Authorization"] = f"Bearer {config.api_key}"
    session = requests.Session()
    retry = Retry(
        total=2,
        read=2,
        connect=2,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset({"POST"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    try:
        response = session.post(url, json=payload, headers=headers, timeout=config.timeout)
        text = response.text
        if not response.ok:
            detail = text if text else "<empty response body>"
            raise RuntimeError(f"LLM request failed with HTTP {response.status_code}: {detail}")
        try:
            return response.json()
        except JSONDecodeError as exc:
            content_type = response.headers.get("Content-Type", "")
            snippet = text[:240].replace("\n", " ").strip()
            raise RuntimeError(
                f"LLM response was not JSON. content-type={content_type!r}, body starts with: {snippet!r}"
            ) from exc
    except requests.RequestException as exc:
        raise RuntimeError(str(exc)) from exc
    finally:
        session.close()


def try_plan_with_llm(
    task: str,
    observation: Observation,
    config: Optional[LLMConfig],
    allow_explicit_submit: bool = False,
) -> Optional[Plan]:
    if not config or not config.enabled:
        return None
    return plan_with_llm(task, observation, config, allow_explicit_submit=allow_explicit_submit)
