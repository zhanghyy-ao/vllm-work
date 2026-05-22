#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_py.llm_planner import LLMConfig, request_text_completion


def main() -> None:
    env_config = LLMConfig.from_env()
    parser = argparse.ArgumentParser(description="Send a minimal request to the configured Gemini/OpenAI-compatible backend.")
    parser.add_argument("--prompt", default="你好，请只回复 ok", help="Prompt to send")
    parser.add_argument("--api-base", default=env_config.api_base, help="LLM API base")
    parser.add_argument("--api-key", default=env_config.api_key, help="LLM API key")
    parser.add_argument("--model", default=env_config.model, help="LLM model")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature")
    args = parser.parse_args()

    config = LLMConfig(
        api_base=args.api_base,
        api_key=args.api_key,
        model=args.model,
        temperature=args.temperature,
    )
    if not config.enabled:
        raise SystemExit("LLM 配置不完整：请检查 .env 中的 BROWSER_AGENT_API_BASE / BROWSER_AGENT_API_KEY / BROWSER_AGENT_MODEL")

    print(
        json.dumps(
            {
                "apiBase": config.api_base,
                "model": config.model,
                "transport": config.transport,
                "prompt": args.prompt,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    try:
        content = request_text_completion(
            [
                {
                    "role": "system",
                    "content": "你是一个简洁的测试助手。严格按用户要求回复，不要补充解释。",
                },
                {"role": "user", "content": args.prompt},
            ],
            config,
            temperature=args.temperature,
        )
    except Exception as exc:
        print("\nREQUEST_FAILED")
        print(str(exc))
        raise SystemExit(1)

    print("\nRESPONSE")
    print(content.strip() or "<empty>")


if __name__ == "__main__":
    main()
