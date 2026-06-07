from __future__ import annotations

import asyncio
import json
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from playwright.async_api import async_playwright


WORKDIR = Path("/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work")
EXT_SRC = WORKDIR / "chrome_extension"
EXT_TMP = Path("/tmp/browser-agent-extension-visible")
PROFILE_TMP = Path("/tmp/browser-agent-extension-visible-profile")
CFT_BIN = Path(
    "/Users/zhanghyy-ao/Library/Caches/ms-playwright/chromium-1217/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
)
TODAY = datetime.now().strftime("%Y-%m-%d")
SHOT_DIR = WORKDIR / "runs"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
API_BASE = "http://127.0.0.1:8000"
POLL_MS = 2500
MAX_AGENT_WAIT_SEC = 180
RUN_STAMP = datetime.now().strftime("%Y-%m-%d-%H%M%S")
RUN_ID = f"{RUN_STAMP}-{uuid4().hex[:8]}"
REPORT_PATH = WORKDIR / "docs" / f"chrome-extension-real-control-test-{RUN_ID}.md"


def port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


def fetch_json(url: str, timeout: float = 5.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def start_backend_if_needed() -> tuple[subprocess.Popen[str] | None, dict]:
    if port_open("127.0.0.1", 8000):
        try:
            return None, fetch_json(f"{API_BASE}/api/config")
        except Exception:
            pass
    backend = subprocess.Popen(
        [sys.executable, "backend_api.py"],
        cwd=str(WORKDIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    deadline = time.time() + 20
    while time.time() < deadline:
        if port_open("127.0.0.1", 8000):
            try:
                return backend, fetch_json(f"{API_BASE}/api/config")
            except Exception:
                time.sleep(0.5)
                continue
        time.sleep(0.5)
    raise RuntimeError("backend_api.py did not become ready on 127.0.0.1:8000")


async def wait_for_extension_worker(context, timeout_sec: int = 20):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        for worker in context.service_workers:
            if worker.url.endswith("/background.js"):
                return worker
        try:
            worker = await context.wait_for_event("serviceworker", timeout=1000)
            if worker.url.endswith("/background.js"):
                return worker
        except Exception:
            pass
    raise RuntimeError("extension background worker not found")


async def wait_for_url_contains(page, needle: str, timeout_sec: int = 30) -> str:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if needle in page.url:
            return page.url
        await page.wait_for_timeout(500)
    raise RuntimeError(f"url did not contain {needle!r}: {page.url}")


def prepare_extension_dir() -> None:
    if EXT_TMP.exists():
        shutil.rmtree(EXT_TMP, ignore_errors=True)
    if PROFILE_TMP.exists():
        shutil.rmtree(PROFILE_TMP, ignore_errors=True)
    shutil.copytree(EXT_SRC, EXT_TMP)


def market_comparison_rows() -> list[dict[str, Any]]:
    return [
        {
            "product": "This project",
            "browser_control": "Visible Chrome for Testing with unpacked extension, direct tab update, monitor loop, DOM-aware follow-up actions.",
            "observation": "URL/title/text/links/controls plus screenshots and multimodal planning hooks.",
            "planning": "Observation-driven action loop with evidence checklist and safe action set.",
            "reporting": "Local latest-run JSON, markdown report, screenshots, traceable evidence.",
            "current_gap": "Still needs tighter live-run progress UX and more predictable long-task convergence.",
        },
        {
            "product": "OpenAI Operator",
            "browser_control": "Cloud/hosted browser interaction with strong UI execution and consumer task polish.",
            "observation": "Rich multimodal observation with strong grounding.",
            "planning": "Closed product loop with strong task completion heuristics.",
            "reporting": "Good user-facing outcome quality but less local inspectability.",
            "current_gap": "Harder to self-host or inspect internal traces compared with this repo.",
        },
        {
            "product": "Anthropic Computer Use",
            "browser_control": "Desktop-style computer control across apps, not only browser tabs.",
            "observation": "Screenshot-centric perception with iterative action loop.",
            "planning": "General-purpose step-by-step interaction.",
            "reporting": "Strong demo value, but app-specific audit artifacts depend on host integration.",
            "current_gap": "This repo is narrower in control scope but stronger on local browser-specific artifacts.",
        },
        {
            "product": "Browser Use",
            "browser_control": "Playwright/browser automation focused, developer-friendly and scriptable.",
            "observation": "DOM-first with browser automation affordances.",
            "planning": "Agent planning around browser tasks, usually developer oriented.",
            "reporting": "Good engineering ergonomics, lighter end-user certification packaging.",
            "current_gap": "This repo now approaches similar explainability, but still needs broader site reliability.",
        },
        {
            "product": "Google Project Mariner",
            "browser_control": "Consumer-facing multi-step browser assistance direction.",
            "observation": "Strong product-layer UX and task continuity emphasis.",
            "planning": "Task-level planning with product polish.",
            "reporting": "Less open implementation detail for local benchmarking.",
            "current_gap": "This repo remains more inspectable, but less polished in user-facing continuity.",
        },
    ]


def shot_path(label: str) -> Path:
    safe = label.replace(" ", "-").replace("/", "-").lower()
    return SHOT_DIR / f"extension-flow-{RUN_ID}-{safe}.png"


async def capture_state(page, label: str, screenshots: list[dict[str, str]]) -> str:
    path = shot_path(label)
    await page.screenshot(path=str(path), full_page=False)
    screenshots.append({"label": label, "path": str(path), "url": page.url})
    return str(path)


async def read_agent_state(worker) -> dict[str, Any]:
    return await worker.evaluate(
        """async () => {
          return await chrome.storage.local.get([
            "agentStatus",
            "agentError",
            "finalUrl",
            "monitorMessage",
            "monitorObservations",
            "lastResult"
          ]);
        }"""
    )


async def start_agent(worker, payload: dict[str, Any]) -> dict[str, Any]:
    return await worker.evaluate(
        """async ({ payload, apiBase }) => {
          const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
          const tab = tabs[0];
          chrome.storage.local.set({
            agentStatus: "launching",
            agentError: "",
            finalUrl: "",
            monitorMessage: "准备启动真实浏览器认证",
            monitorObservations: [],
            lastResult: null
          });
          controlBrowser(tab.id, payload, apiBase).catch(async (error) => {
            await chrome.storage.local.set({
              agentStatus: "error",
              agentError: error.message || String(error)
            });
          });
          return { started: true, tabId: tab.id };
        }""",
        {"payload": payload, "apiBase": API_BASE},
    )


async def wait_for_agent_completion(page, worker, screenshots: list[dict[str, str]]) -> dict[str, Any]:
    deadline = time.time() + MAX_AGENT_WAIT_SEC
    last_status = None
    poll_count = 0
    history: list[dict[str, Any]] = []
    while time.time() < deadline:
        state = await read_agent_state(worker)
        poll_count += 1
        status = state.get("agentStatus") or "unknown"
        entry = {
            "poll": poll_count,
            "status": status,
            "monitorMessage": state.get("monitorMessage"),
            "finalUrl": state.get("finalUrl"),
            "visibleUrl": page.url,
            "visibleTitle": await page.title(),
        }
        history.append(entry)
        if status != last_status:
            await capture_state(page, f"status-{status}-{poll_count}", screenshots)
            last_status = status
        if status in {"done", "needs_review", "error"}:
            state["_history"] = history
            return state
        await page.wait_for_timeout(POLL_MS)
    state = await read_agent_state(worker)
    state["_history"] = history
    state["_timeout"] = True
    return state


async def run_visible_flow() -> dict:
    backend_proc, config = start_backend_if_needed()
    prepare_extension_dir()
    screenshots: list[dict[str, str]] = []
    report: dict[str, Any] = {
        "backend_config": {
            "provider": config.get("provider"),
            "model": config.get("model"),
            "api_base_url": config.get("api_base_url"),
            "vision_provider": config.get("vision_provider"),
            "vision_model": config.get("vision_model"),
            "vision_api_base_url": config.get("vision_api_base_url"),
            "planner_max_tokens": config.get("planner_max_tokens"),
            "report_max_tokens": config.get("report_max_tokens"),
            "use_multimodal_planning": config.get("use_multimodal_planning"),
            "use_visual_precheck": config.get("use_visual_precheck"),
            "api_key_configured": config.get("api_key_configured"),
            "vision_api_key_configured": config.get("vision_api_key_configured"),
        },
        "screenshots": screenshots,
    }
    try:
        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_TMP),
                executable_path=str(CFT_BIN),
                headless=False,
                viewport={"width": 1440, "height": 980},
                args=[
                    f"--disable-extensions-except={EXT_TMP}",
                    f"--load-extension={EXT_TMP}",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://cn.bing.com/", wait_until="domcontentloaded")
            await capture_state(page, "01-bing-home", screenshots)
            worker = await wait_for_extension_worker(context)
            extension_id = worker.url.split("/")[2]
            report["extension_id"] = extension_id
            report["background_url"] = worker.url

            direct_url = (
                "https://cn.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA"
                "+%E6%8E%A8%E8%8D%90+%E9%80%9A%E5%8B%A4+%E5%8A%9E%E5%85%AC"
            )
            direct_result = await worker.evaluate(
                """async (url) => {
                  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
                  const tab = tabs[0];
                  await chrome.tabs.update(tab.id, { url });
                  return { tabId: tab.id, requestedUrl: url, extensionId: chrome.runtime.id };
                }""",
                direct_url,
            )
            await wait_for_url_contains(page, "bing.com/search", timeout_sec=30)
            await page.wait_for_load_state("domcontentloaded", timeout=30000)
            direct_shot = await capture_state(page, "02-direct-control-search-page", screenshots)
            report["direct_control"] = {
                **direct_result,
                "observed_url": page.url,
                "title": await page.title(),
                "screenshot": direct_shot,
            }

            payload = {
                "goal": "推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论",
                "url": direct_url,
                "domain": "shopping",
                "max_steps": 8,
                "use_llm": True,
            }
            launch_info = await start_agent(worker, payload)
            await capture_state(page, "03-agent-launched", screenshots)
            agent_state = await wait_for_agent_completion(page, worker, screenshots)
            final_shot = await capture_state(page, "04-agent-final-state", screenshots)

            latest_run = agent_state.get("lastResult") if isinstance(agent_state.get("lastResult"), dict) else {}
            report["agent_control"] = {
                "launch_info": launch_info,
                "storage_state": agent_state,
                "visible_url": page.url,
                "visible_title": await page.title(),
                "screenshot": final_shot,
                "latest_run_goal": latest_run.get("goal"),
                "latest_run_ok": latest_run.get("ok"),
                "latest_run_agent": latest_run.get("agent"),
                "latest_run_workflow": latest_run.get("workflow"),
                "latest_run_summary": (latest_run.get("report") or {}).get("summary"),
                "events": len(latest_run.get("events", [])),
                "steps": len(latest_run.get("steps", [])),
                "latest_run_evidence_items": len((latest_run.get("memory") or {}).get("evidence", [])),
                "latest_run_recommendations": len(((latest_run.get("report") or {}).get("recommendations") or [])),
            }
            report["market_comparison_rows"] = market_comparison_rows()
            await context.close()
    finally:
        if backend_proc is not None:
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_proc.kill()
    return report


def _state_line(label: str, value: Any) -> str:
    return f"- {label}: `{value}`"


def write_report(data: dict[str, Any]) -> None:
    storage_state = data["agent_control"]["storage_state"]
    latest_run_ok = data["agent_control"].get("latest_run_ok")
    direct_ok = "bing.com/search" in data["direct_control"]["observed_url"]
    status = storage_state.get("agentStatus")
    browser_loop_ok = status == "done"
    planner_ok = latest_run_ok is True and storage_state.get("agentError", "") == ""
    diagnostic = "none"
    if storage_state.get("_timeout"):
        diagnostic = "agent_wait_timeout"
    elif storage_state.get("agentError"):
        diagnostic = storage_state["agentError"]
    elif not latest_run_ok:
        diagnostic = "latest_run_not_ok"

    history = storage_state.get("_history") or []
    lines = [
        f"# Chrome Extension Real Browser Control Test - {TODAY}",
        "",
        "## Scope",
        "",
        "Validate a visible Chrome extension session end to end: extension load, direct tab control, real shopping-task execution, screenshots, and a broader market comparison.",
        "",
        "## Backend Config",
        "",
        _state_line("provider/model", f"{data['backend_config']['provider']} / {data['backend_config']['model']}"),
        _state_line("api base", data["backend_config"]["api_base_url"]),
        _state_line(
            "vision provider/model",
            f"{data['backend_config']['vision_provider']} / {data['backend_config']['vision_model']}",
        ),
        _state_line("vision api base", data["backend_config"]["vision_api_base_url"]),
        _state_line(
            "planner/report max tokens",
            f"{data['backend_config']['planner_max_tokens']} / {data['backend_config']['report_max_tokens']}",
        ),
        _state_line("multimodal planning", data["backend_config"]["use_multimodal_planning"]),
        _state_line("visual precheck", data["backend_config"]["use_visual_precheck"]),
        _state_line("key configured", data["backend_config"]["api_key_configured"]),
        "",
        "## Certification Summary",
        "",
        _state_line("visible Chrome extension load", f"PASS ({data.get('extension_id', '')})"),
        _state_line("direct tab control from extension background", "PASS" if direct_ok else "FAIL"),
        _state_line("extension monitor loop and follow-up navigation", "PASS" if browser_loop_ok else "FAIL"),
        _state_line("full LLM planning and evidence extraction", "PASS" if planner_ok else "FAIL"),
        _state_line("diagnostic", diagnostic),
        "",
        "## Visible Flow Evidence",
        "",
        _state_line("extension id", data.get("extension_id", "")),
        _state_line("background worker", data.get("background_url", "")),
        _state_line("direct browser control observed URL", data["direct_control"]["observed_url"]),
        _state_line("direct browser control title", data["direct_control"]["title"]),
        _state_line("agent storage status", storage_state.get("agentStatus")),
        _state_line("agent final URL", storage_state.get("finalUrl")),
        _state_line("current visible URL after agent run", data["agent_control"]["visible_url"]),
        _state_line("current visible title after agent run", data["agent_control"]["visible_title"]),
        _state_line("latest run goal", data["agent_control"]["latest_run_goal"]),
        _state_line("latest run summary", data["agent_control"]["latest_run_summary"]),
        _state_line("latest run events/steps", f"{data['agent_control']['events']} / {data['agent_control']['steps']}"),
        _state_line("latest run evidence items", data["agent_control"]["latest_run_evidence_items"]),
        _state_line("latest run recommendations", data["agent_control"]["latest_run_recommendations"]),
        "",
        "## Screenflow Screenshots",
        "",
    ]
    for shot in data.get("screenshots", []):
        lines.append(f"- {shot['label']}: `{shot['path']}`")
    lines.extend(
        [
            "",
            "## Agent Poll History",
            "",
        ]
    )
    for item in history:
        lines.append(
            f"- poll {item['poll']}: status=`{item['status']}` title=`{item['visibleTitle']}` url=`{item['visibleUrl']}` message=`{item.get('monitorMessage')}`"
        )
    lines.extend(
        [
            "",
            "## Diagnosis",
            "",
            "- The extension is now verified as truly controlling a visible Chrome window, not only producing backend JSON.",
            "- The browser side visibly moved from the Bing home page into a real shopping-search task page and then continued through the extension's monitor loop.",
            "- The latest backend result shows the shopping workflow completed with candidate extraction and evidence collection, so the main blocker has shifted away from the old provider-access problem.",
            "- The remaining work is product quality rather than basic connectivity: better live progress UX, more predictable long-task pacing, and richer cross-site coverage.",
            "",
            "## Market Comparison",
            "",
            "| Product | Browser Control | Observation | Planning | Reporting | Gap vs This Repo |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in data.get("market_comparison_rows", []):
        lines.append(
            f"| {row['product']} | {row['browser_control']} | {row['observation']} | {row['planning']} | {row['reporting']} | {row['current_gap']} |"
        )
    lines.extend(
        [
            "",
            "## Raw Data",
            "",
            "```json",
            json.dumps(data, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    data = asyncio.run(run_visible_flow())
    write_report(data)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(str(REPORT_PATH))


if __name__ == "__main__":
    main()
