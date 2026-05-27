from __future__ import annotations

import argparse
import json
from pathlib import Path

from browser_agent.harness.runtime import HarnessRuntime


def main() -> None:
    parser = argparse.ArgumentParser(description="Browser Copilot Agent entrypoint")
    parser.add_argument("--goal", required=True, help="User goal")
    parser.add_argument("--url", default="https://example.com", help="Start URL")
    parser.add_argument("--max-steps", type=int, default=8, help="Max loop steps")
    args = parser.parse_args()

    runtime = HarnessRuntime(max_steps=args.max_steps)
    result = runtime.run(goal=args.goal, start_url=args.url)

    out_dir = Path("runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "latest-run.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nSaved: {out_file}")


if __name__ == "__main__":
    main()
