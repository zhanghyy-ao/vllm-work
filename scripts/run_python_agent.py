#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_py import BrowserHarness, observe_html, plan_task


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Python browser-agent harness on a local HTML file.")
    parser.add_argument("task", help="Natural language task, e.g. '搜索 多模态大模型'")
    parser.add_argument("--html", default="demo-site/index.html", help="HTML file to observe")
    parser.add_argument("--url", default="http://127.0.0.1:8765", help="Source URL shown in artifacts")
    args = parser.parse_args()

    html = Path(args.html).read_text(encoding="utf-8")
    observation = observe_html(html, url=args.url)
    plan = plan_task(args.task, observation)
    result = BrowserHarness(observation).run(plan)

    print("PLAN")
    print(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2))
    print("\nRESULT")
    print(
        json.dumps(
            {
                "ok": result.ok,
                "url": result.url,
                "artifact": result.artifact,
                "logs": [
                    {
                        "action": item.action.to_dict(),
                        "ok": item.ok,
                        "output": item.output,
                        "error": item.error,
                    }
                    for item in result.logs
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
