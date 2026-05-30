from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class AgentConfig:
    agent_name: str = "browser-workflow-agent"
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    api_key_env: str = "DEEPSEEK_API_KEY"
    api_base_url: str = "https://api.deepseek.com"
    use_llm: bool = False
    vision_provider: str = "gemini"
    vision_model: str = "gemini-1.5-flash"
    vision_api_key_env: str = "GEMINI_API_KEY"

    @property
    def api_key_configured(self) -> bool:
        return bool(os.getenv(self.api_key_env))

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        data["api_key_configured"] = self.api_key_configured
        data["vision_api_key_configured"] = bool(os.getenv(self.vision_api_key_env))
        data.pop("api_key_env", None)
        data.pop("vision_api_key_env", None)
        return data


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
    api_key_env: Optional[str] = None,
    api_base_url: Optional[str] = None,
    use_llm: bool = False,
    vision_provider: Optional[str] = None,
    vision_model: Optional[str] = None,
    vision_api_key_env: Optional[str] = None,
) -> AgentConfig:
    load_dotenv()
    return AgentConfig(
        agent_name=agent_name or os.getenv("BROWSER_AGENT_NAME", AgentConfig.agent_name),
        provider=provider or os.getenv("BROWSER_AGENT_PROVIDER", AgentConfig.provider),
        model=model or os.getenv("BROWSER_AGENT_MODEL", AgentConfig.model),
        api_key_env=api_key_env or os.getenv("BROWSER_AGENT_API_KEY_ENV", AgentConfig.api_key_env),
        api_base_url=api_base_url or os.getenv("BROWSER_AGENT_API_BASE_URL", AgentConfig.api_base_url),
        use_llm=use_llm or os.getenv("BROWSER_AGENT_USE_LLM", "").lower() in {"1", "true", "yes"},
        vision_provider=vision_provider or os.getenv("BROWSER_AGENT_VISION_PROVIDER", AgentConfig.vision_provider),
        vision_model=vision_model or os.getenv("BROWSER_AGENT_VISION_MODEL", AgentConfig.vision_model),
        vision_api_key_env=vision_api_key_env or os.getenv("BROWSER_AGENT_VISION_API_KEY_ENV", AgentConfig.vision_api_key_env),
    )
