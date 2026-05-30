from __future__ import annotations

import argparse
import json
from pathlib import Path

from browser_agent.config import build_agent_config
from browser_agent.harness.runtime import HarnessRuntime
from browser_agent.output.markdown import render_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Browser Copilot Agent entrypoint")
    parser.add_argument("--goal", required=True, help="User goal")
    parser.add_argument("--url", default="https://example.com", help="Start URL")
    parser.add_argument("--domain", default="auto", choices=["auto", "github", "paper", "shopping", "video", "general"], help="Workflow domain")
    parser.add_argument("--max-steps", type=int, default=8, help="Max loop steps")
    parser.add_argument("--headed", action="store_true", help="Run browser with a visible window")
    parser.add_argument("--agent-name", default=None, help="Agent name recorded in run metadata")
    parser.add_argument("--provider", default=None, help="LLM/API provider name, e.g. deepseek")
    parser.add_argument("--model", default=None, help="Model name recorded in run metadata")
    parser.add_argument("--api-key-env", default=None, help="Environment variable containing the provider API key")
    parser.add_argument("--api-base-url", default=None, help="Provider API base URL")
    parser.add_argument("--use-llm", action="store_true", help="Enable configured LLM usage when planner/summarizer support is added")
    parser.add_argument("--vision-provider", default=None, help="Optional multimodal provider, e.g. gemini")
    parser.add_argument("--vision-model", default=None, help="Optional multimodal model name")
    parser.add_argument("--vision-api-key-env", default=None, help="Environment variable containing the multimodal provider API key")
    args = parser.parse_args()

    agent_config = build_agent_config(
        agent_name=args.agent_name,
        provider=args.provider,
        model=args.model,
        api_key_env=args.api_key_env,
        api_base_url=args.api_base_url,
        use_llm=args.use_llm,
        vision_provider=args.vision_provider,
        vision_model=args.vision_model,
        vision_api_key_env=args.vision_api_key_env,
    )
    runtime = HarnessRuntime(max_steps=args.max_steps, headless=not args.headed, agent_config=agent_config)
    result = runtime.run(goal=args.goal, start_url=args.url, domain=args.domain)

    out_dir = Path("runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "latest-run.json"
    report_file = out_dir / "latest-report.md"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report_file.write_text(render_markdown_report(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nSaved: {out_file}")
    print(f"Report: {report_file}")


if __name__ == "__main__":
    main()
