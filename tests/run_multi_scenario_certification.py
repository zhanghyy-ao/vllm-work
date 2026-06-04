from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


WORKDIR = Path("/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work")
TODAY = datetime.now().strftime("%Y-%m-%d")
OUT_JSON = WORKDIR / "runs" / f"multi-scenario-certification-{TODAY}.json"
OUT_MD = WORKDIR / "docs" / f"multi-scenario-certification-{TODAY}.md"
LATEST_RUN = WORKDIR / "runs" / "latest-run.json"
TIMEOUT_SEC = 120


SCENARIOS = [
    {
        "name": "shopping",
        "goal": "推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论",
        "url": "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC",
        "domain": "shopping",
        "max_steps": 3,
    },
    {
        "name": "github",
        "goal": "帮我找几个可以参考的浏览器自动化智能体 GitHub 开源项目，比较活跃度、语言、README质量和适合借鉴的实现点",
        "url": "https://github.com",
        "domain": "github",
        "max_steps": 3,
    },
    {
        "name": "video",
        "goal": "帮我查找并整理一个 CLIP 多模态模型入门教程视频的主要内容",
        "url": "https://www.bing.com/videos/",
        "domain": "video",
        "max_steps": 3,
    },
]


def scenario_run_path(name: str) -> Path:
    return WORKDIR / "runs" / f"latest-run-{name}-current.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _scenario_summary(name: str, result: dict[str, Any], timeout: bool = False, error: str = "") -> dict[str, Any]:
    report = result.get("report") or {}
    memory = result.get("memory") or {}
    return {
        "name": name,
        "ok": result.get("ok"),
        "timeout": timeout,
        "error": error,
        "goal": result.get("goal"),
        "summary": report.get("summary"),
        "steps": len(result.get("steps") or []),
        "events": len(result.get("events") or []),
        "evidence_items": len(memory.get("evidence") or []),
        "recommendations": len(report.get("recommendations") or []),
        "comparison_rows": len(report.get("comparison_matrix") or []),
        "next_actions": len(report.get("next_actions") or []),
    }


def run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "app.py",
        "--goal",
        scenario["goal"],
        "--url",
        scenario["url"],
        "--domain",
        scenario["domain"],
        "--max-steps",
        str(scenario["max_steps"]),
        "--use-llm",
    ]
    try:
        subprocess.run(
            cmd,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired as exc:
        result = _read_json(LATEST_RUN) if LATEST_RUN.exists() else {"goal": scenario["goal"], "ok": False}
        return _scenario_summary(scenario["name"], result, timeout=True, error=str(exc))
    except subprocess.CalledProcessError as exc:
        result = _read_json(LATEST_RUN) if LATEST_RUN.exists() else {"goal": scenario["goal"], "ok": False}
        return _scenario_summary(scenario["name"], result, timeout=False, error=exc.stderr[-500:] if exc.stderr else str(exc))

    result = _read_json(LATEST_RUN)
    shutil.copy2(LATEST_RUN, scenario_run_path(scenario["name"]))
    return _scenario_summary(scenario["name"], result)


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        f"# Multi-Scenario Certification - {TODAY}",
        "",
        "## Scope",
        "",
        "Re-run representative browser-agent scenarios on the current codebase and summarize execution quality, evidence collection, and report completeness.",
        "",
        "## Scenario Results",
        "",
        "| Scenario | OK | Timeout | Steps | Events | Evidence | Recommendations | Comparison Rows | Summary |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in payload["scenarios"]:
        summary = (item["summary"] or "").replace("|", "/")
        lines.append(
            f"| {item['name']} | {item['ok']} | {item['timeout']} | {item['steps']} | {item['events']} | {item['evidence_items']} | {item['recommendations']} | {item['comparison_rows']} | {summary[:160]} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `shopping` emphasizes candidate collection, marketplace grounding, and recommendation structure.",
            "- `github` emphasizes repository discovery, metadata extraction, and comparison reporting.",
            "- `video` emphasizes video-link discovery, page digestion, and tutorial-style summarization.",
            "",
            "## Scenario Run Files",
            "",
        ]
    )
    for item in payload["scenarios"]:
        lines.append(f"- `{item['name']}`: `runs/latest-run-{item['name']}-current.json`")
    lines.extend(
        [
            "",
            "## Raw JSON",
            "",
            "```json",
            json.dumps(payload, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    outputs = [run_scenario(scenario) for scenario in SCENARIOS]
    payload = {
        "generated_at": datetime.now().isoformat(),
        "timeout_sec_per_scenario": TIMEOUT_SEC,
        "scenarios": outputs,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(str(OUT_MD))


if __name__ == "__main__":
    main()
