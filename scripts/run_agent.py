#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_py import BrowserAgentRunner, LLMConfig
from agent_py.runner import save_trajectory


def main() -> None:
    env_config = LLMConfig.from_env()
    parser = argparse.ArgumentParser(description="Run the Python-only browser agent on a real browser page.")
    parser.add_argument("--url", required=True, help="URL to open")
    parser.add_argument("--task", required=True, help="Natural language task")
    parser.add_argument("--api-base", default=env_config.api_base, help="OpenAI-compatible API base")
    parser.add_argument("--api-key", default=env_config.api_key, help="API key. If omitted, use rule planner.")
    parser.add_argument("--model", default=env_config.model, help="Model name. If omitted, use rule planner.")
    parser.add_argument("--headless", action="store_true", help="Run Chromium headless")
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222", help="Connect to an existing Chrome/Chromium remote debugging endpoint. Use empty string to force temporary Chromium.")
    parser.add_argument("--max-steps", type=int, default=8, help="Maximum actions to execute")
    parser.add_argument("--allow-explicit-submit", action="store_true", help="Allow explicit user-requested submit/send/publish actions except hard-risk actions")
    parser.add_argument("--screenshot-dir", default="runs/screenshots", help="Directory for observation screenshots")
    parser.add_argument("--slow-mo", type=int, default=250, help="Delay Playwright actions in milliseconds for visible demos")
    parser.add_argument("--linger", type=float, default=8, help="Seconds to keep the visible temporary browser open after execution")
    parser.add_argument("--trajectory", default="runs/trajectory.json", help="Path to save trajectory JSON")
    args = parser.parse_args()

    config = LLMConfig(api_base=args.api_base, api_key=args.api_key, model=args.model)
    result = BrowserAgentRunner(
        llm_config=config,
        headless=args.headless,
        cdp_url=args.cdp_url,
        max_steps=args.max_steps,
        slow_mo=args.slow_mo,
        screenshot_dir=args.screenshot_dir,
        allow_explicit_submit=args.allow_explicit_submit,
        linger_seconds=0 if args.headless else args.linger,
    ).run(args.url, args.task)
    save_trajectory(result, args.trajectory)

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    print(f"\nSaved trajectory: {args.trajectory}")


if __name__ == "__main__":
    main()
