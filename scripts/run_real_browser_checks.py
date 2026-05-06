#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_py import BrowserAgentRunner, LLMConfig
from agent_py.runner import save_trajectory


TASKS = [
    "搜索 多模态大模型",
    "填写 姓名=张三 邮箱=zhangsan@example.com 主题=多模态智能体 备注=这是课程 Demo",
    "回复小明：我今晚八点前把材料发你",
    "分析这个界面能做什么",
    "比较这些浏览器智能体方案",
    "提取页面链接和邮箱",
    "帮忙查找 Browser Harness",
    "打开 Browser Harness",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run end-to-end checks against a real CDP-controlled browser.")
    parser.add_argument("--url", default="http://127.0.0.1:8765", help="Demo URL")
    parser.add_argument("--port", type=int, default=9223, help="Temporary CDP port")
    parser.add_argument("--headed", action="store_true", help="Show the browser window while checks run")
    parser.add_argument("--slow-mo", type=int, default=80, help="Visible action delay in milliseconds")
    parser.add_argument("--output-dir", default="runs/real-browser-checks", help="Where trajectories/screenshots are written")
    args = parser.parse_args()

    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    demo_proc = _ensure_demo_server(args.url)
    chrome_proc = None
    profile_dir = Path(tempfile.mkdtemp(prefix="browser-agent-cdp-"))
    try:
        chrome_proc = _launch_cdp_chromium(args.port, profile_dir, args.url, headless=not args.headed)
        _wait_for_url(f"http://127.0.0.1:{args.port}/json/version", timeout=12)
        results = []
        for index, task in enumerate(TASKS, start=1):
            trajectory_path = output_dir / f"task-{index:02d}.json"
            screenshot_dir = output_dir / f"screenshots-{index:02d}"
            result = BrowserAgentRunner(
                llm_config=LLMConfig(api_key="", model=""),
                headless=not args.headed,
                cdp_url=f"http://127.0.0.1:{args.port}",
                max_steps=8,
                slow_mo=args.slow_mo,
                screenshot_dir=str(screenshot_dir),
            ).run(args.url, task)
            save_trajectory(result, str(trajectory_path))
            _assert_result(task, result.to_dict())
            results.append({"task": task, "trajectory": str(trajectory_path), "artifactLength": len(result.execution.artifact)})
            print(f"ok {index}/{len(TASKS)}: {task}")
        summary = output_dir / "summary.json"
        summary.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"All real-browser checks passed. Summary: {summary}")
    finally:
        if chrome_proc:
            chrome_proc.terminate()
        if demo_proc:
            demo_proc.terminate()
        shutil.rmtree(profile_dir, ignore_errors=True)


def _ensure_demo_server(url: str) -> subprocess.Popen[Any] | None:
    if _url_ready(url):
        return None
    proc = subprocess.Popen([sys.executable, str(ROOT / "scripts" / "serve_demo.py")], cwd=str(ROOT))
    _wait_for_url(url, timeout=8)
    return proc


def _launch_cdp_chromium(port: int, profile_dir: Path, url: str, headless: bool) -> subprocess.Popen[Any]:
    from playwright.sync_api import sync_playwright

    playwright = sync_playwright().start()
    try:
        executable = playwright.chromium.executable_path
    finally:
        playwright.stop()
    command = [
        executable,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-default-apps",
    ]
    if headless:
        command.extend(["--headless=new", "--disable-gpu"])
    command.append(url)
    return subprocess.Popen(command, cwd=str(ROOT))


def _assert_result(task: str, data: dict[str, Any]) -> None:
    if data.get("browserMode") != "cdp-attached":
        raise AssertionError(f"{task}: expected cdp-attached, got {data.get('browserMode')}")
    execution = data.get("execution", {})
    if not execution.get("ok"):
        raise AssertionError(f"{task}: execution failed")
    if not str(execution.get("artifact") or "").strip():
        raise AssertionError(f"{task}: artifact is empty")
    trajectory = execution.get("trajectory") or []
    if not trajectory:
        raise AssertionError(f"{task}: trajectory is empty")


def _wait_for_url(url: str, timeout: float) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _url_ready(url):
            return
        time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for {url}")


def _url_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=0.5) as response:
            return 200 <= response.status < 500
    except Exception:
        return False


if __name__ == "__main__":
    main()
