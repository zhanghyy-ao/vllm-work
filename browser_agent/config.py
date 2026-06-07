from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class AgentConfig:
    agent_name: str = "browser-workflow-agent"
    provider: str = "openai_compatible"
    model: str = "gpt-5.4"
    model_fallbacks: list[str] = field(default_factory=lambda: ["gpt-5.4", "gpt-5.4-mini"])
    api_key_env: str = "BROWSER_AGENT_API_KEY"
    api_base_url: str = "https://synai996.space/v1"
    use_llm: bool = False
    vision_provider: str = "openai_compatible"
    vision_model: str = "gpt-5.4"
    vision_model_fallbacks: list[str] = field(default_factory=lambda: ["gpt-5.4", "gpt-5.4-mini"])
    vision_api_key_env: str = "BROWSER_AGENT_API_KEY"
    vision_api_base_url: str = "https://synai996.space/v1"
    http_user_agent: str = "codex-browser-agent/1.0"
    llm_timeout_sec: int = 30
    vision_timeout_sec: int = 30
    planner_max_tokens: int = 1000
    report_max_tokens: int = 1600
    report_retry_max_tokens: int = 900
    use_multimodal_planning: bool = True
    use_visual_precheck: bool = False

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key_value)

    @property
    def api_key_value(self) -> str:
        return _compatible_api_key_value(self.api_key_env)

    @property
    def vision_api_key_value(self) -> str:
        return _compatible_api_key_value(self.vision_api_key_env)

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        data["api_key_configured"] = self.api_key_configured
        data["vision_api_key_configured"] = bool(self.vision_api_key_value)
        data.pop("api_key_env", None)
        data.pop("vision_api_key_env", None)
        return data


def _first_env_value(*names: str) -> str:
    seen = set()
    for name in names:
        if not name or name in seen:
            continue
        seen.add(name)
        value = os.getenv(name)
        if value:
            return value
    return ""


def _compatible_api_key_value(primary_env: str) -> str:
    if primary_env and primary_env != "BROWSER_AGENT_API_KEY":
        return os.getenv(primary_env, "")
    return _first_env_value("BROWSER_AGENT_API_KEY", "SYNAI_API_KEY", "OPENAI_API_KEY")


def _csv_env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name, "")
    if not raw.strip():
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def build_agent_config(
    agent_name: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    model_fallbacks: Optional[list[str]] = None,
    api_key_env: Optional[str] = None,
    api_base_url: Optional[str] = None,
    use_llm: bool = False,
    vision_provider: Optional[str] = None,
    vision_model: Optional[str] = None,
    vision_model_fallbacks: Optional[list[str]] = None,
    vision_api_key_env: Optional[str] = None,
    vision_api_base_url: Optional[str] = None,
    http_user_agent: Optional[str] = None,
    llm_timeout_sec: Optional[int] = None,
    vision_timeout_sec: Optional[int] = None,
    planner_max_tokens: Optional[int] = None,
    report_max_tokens: Optional[int] = None,
    report_retry_max_tokens: Optional[int] = None,
    use_multimodal_planning: Optional[bool] = None,
    use_visual_precheck: Optional[bool] = None,
) -> AgentConfig:
    load_dotenv()
    return AgentConfig(
        agent_name=agent_name or os.getenv("BROWSER_AGENT_NAME", AgentConfig.agent_name),
        provider=provider or os.getenv("BROWSER_AGENT_PROVIDER", AgentConfig.provider),
        model=model or os.getenv("BROWSER_AGENT_MODEL", AgentConfig.model),
        model_fallbacks=model_fallbacks or _csv_env_list("BROWSER_AGENT_MODEL_FALLBACKS", AgentConfig().model_fallbacks),
        api_key_env=api_key_env or os.getenv("BROWSER_AGENT_API_KEY_ENV", AgentConfig.api_key_env),
        api_base_url=api_base_url or os.getenv("BROWSER_AGENT_API_BASE_URL", AgentConfig.api_base_url),
        use_llm=use_llm or os.getenv("BROWSER_AGENT_USE_LLM", "").lower() in {"1", "true", "yes"},
        vision_provider=vision_provider or os.getenv("BROWSER_AGENT_VISION_PROVIDER", AgentConfig.vision_provider),
        vision_model=vision_model or os.getenv("BROWSER_AGENT_VISION_MODEL", AgentConfig.vision_model),
        vision_model_fallbacks=vision_model_fallbacks
        or _csv_env_list("BROWSER_AGENT_VISION_MODEL_FALLBACKS", AgentConfig().vision_model_fallbacks),
        vision_api_key_env=vision_api_key_env or os.getenv("BROWSER_AGENT_VISION_API_KEY_ENV", AgentConfig.vision_api_key_env),
        vision_api_base_url=vision_api_base_url or os.getenv("BROWSER_AGENT_VISION_API_BASE_URL", AgentConfig.vision_api_base_url),
        http_user_agent=http_user_agent or os.getenv("BROWSER_AGENT_HTTP_USER_AGENT", AgentConfig.http_user_agent),
        llm_timeout_sec=int(llm_timeout_sec or os.getenv("BROWSER_AGENT_LLM_TIMEOUT_SEC", AgentConfig.llm_timeout_sec)),
        vision_timeout_sec=int(vision_timeout_sec or os.getenv("BROWSER_AGENT_VISION_TIMEOUT_SEC", AgentConfig.vision_timeout_sec)),
        planner_max_tokens=int(planner_max_tokens or os.getenv("BROWSER_AGENT_PLANNER_MAX_TOKENS", AgentConfig.planner_max_tokens)),
        report_max_tokens=int(report_max_tokens or os.getenv("BROWSER_AGENT_REPORT_MAX_TOKENS", AgentConfig.report_max_tokens)),
        report_retry_max_tokens=int(
            report_retry_max_tokens or os.getenv("BROWSER_AGENT_REPORT_RETRY_MAX_TOKENS", AgentConfig.report_retry_max_tokens)
        ),
        use_multimodal_planning=(
            use_multimodal_planning
            if use_multimodal_planning is not None
            else os.getenv("BROWSER_AGENT_USE_MULTIMODAL_PLANNING", "true").lower() in {"1", "true", "yes"}
        ),
        use_visual_precheck=(
            use_visual_precheck
            if use_visual_precheck is not None
            else os.getenv("BROWSER_AGENT_USE_VISUAL_PRECHECK", "").lower() in {"1", "true", "yes"}
        ),
    )
