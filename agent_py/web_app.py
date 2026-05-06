from __future__ import annotations

import html
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict

from .llm_planner import LLMConfig
from .runner import BrowserAgentRunner, save_trajectory


LAST_RESULT: Dict[str, Any] = {}


def create_app():
    try:
        from flask import Flask, Response, abort, redirect, render_template_string, request, send_file, url_for
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Flask is not installed. Run: python3 -m pip install -r requirements.txt") from exc

    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index():
        global LAST_RESULT
        env_config = LLMConfig.from_env()
        api_key_input = request.form.get("api_key", "") if request.method == "POST" else ""
        form = {
            "url": request.form.get("url", "http://127.0.0.1:8765"),
            "task": request.form.get("task", "分析这个界面能做什么"),
            "api_base": request.form.get("api_base", env_config.api_base),
            "api_key": "",
            "api_key_configured": bool(api_key_input or env_config.api_key),
            "model": request.form.get("model", env_config.model),
            "cdp_url": request.form.get("cdp_url", "http://127.0.0.1:9222"),
            "max_steps": request.form.get("max_steps", "8"),
            "screenshot_dir": request.form.get("screenshot_dir", "runs/screenshots"),
            "slow_mo": request.form.get("slow_mo", "350"),
            "linger": request.form.get("linger", "8"),
            "headless": request.form.get("headless") == "on",
            "allow_explicit_submit": request.form.get("allow_explicit_submit") == "on",
        }
        error = ""
        cdp_status = _check_cdp(form["cdp_url"])
        if request.method == "POST":
            try:
                config = LLMConfig(api_base=form["api_base"], api_key=api_key_input or env_config.api_key, model=form["model"])
                slow_mo = int(form["slow_mo"] or 0)
                linger = float(form["linger"] or 0)
                max_steps = int(form["max_steps"] or 6)
                result = BrowserAgentRunner(
                    llm_config=config,
                    headless=form["headless"],
                    cdp_url=form["cdp_url"],
                    max_steps=max_steps,
                    slow_mo=slow_mo,
                    screenshot_dir=form["screenshot_dir"],
                    allow_explicit_submit=form["allow_explicit_submit"],
                    linger_seconds=0 if form["headless"] else linger,
                ).run(form["url"], form["task"])
                LAST_RESULT = result.to_dict()
            except Exception as exc:
                error = str(exc)

        return render_template_string(
            TEMPLATE,
            form=form,
            result=LAST_RESULT,
            error=error,
            pretty=_pretty,
            cdp_status=cdp_status,
            screenshots=_screenshots(LAST_RESULT),
            quote=urllib.parse.quote,
        )

    @app.route("/download/trajectory.json")
    def download_trajectory():
        if not LAST_RESULT:
            return redirect(url_for("index"))
        body = json.dumps(LAST_RESULT, ensure_ascii=False, indent=2)
        return Response(
            body,
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=trajectory.json"},
        )

    @app.route("/artifact/screenshot")
    def screenshot_artifact():
        raw_path = request.args.get("path", "")
        if not raw_path:
            abort(404)
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        try:
            resolved = path.resolve()
        except Exception:
            abort(404)
        if resolved.suffix.lower() != ".png" or not resolved.exists():
            abort(404)
        return send_file(resolved, mimetype="image/png")

    return app


def run_app(host: str = "127.0.0.1", port: int = 8787, debug: bool = False) -> None:
    create_app().run(host=host, port=port, debug=debug)


def _pretty(value: Any) -> str:
    return html.escape(json.dumps(value, ensure_ascii=False, indent=2))


def _check_cdp(cdp_url: str) -> str:
    if not cdp_url:
        return "未填写 CDP URL，将使用临时 Chromium。"
    try:
        with urllib.request.urlopen(cdp_url.rstrip("/") + "/json/version", timeout=0.8) as response:
            data = json.loads(response.read().decode("utf-8"))
            return f"已检测到 Chrome CDP：{data.get('Browser', 'Chrome')}"
    except Exception:
        return "未检测到 Chrome CDP；运行时会自动回退到临时 Chromium。"


def _screenshots(result: Dict[str, Any]) -> list[str]:
    if not result:
        return []
    paths: list[str] = []
    execution = result.get("execution", {})
    for entry in execution.get("trajectory", []) if isinstance(execution, dict) else []:
        if not isinstance(entry, dict):
            continue
        observation = entry.get("observation", {})
        if not isinstance(observation, dict):
            continue
        path = str(observation.get("screenshotPath") or "")
        if path and path not in paths:
            paths.append(path)
    return paths[-6:]


TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Python Browser Agent</title>
  <style>
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; background: #f6efe3; color: #17211c; }
    main { max-width: 1120px; margin: 0 auto; padding: 36px 22px 72px; }
    h1 { margin: 0 0 8px; font-size: 38px; letter-spacing: -0.04em; }
    .subtitle { color: #667064; margin-bottom: 24px; }
    .grid { display: grid; grid-template-columns: minmax(280px, 420px) 1fr; gap: 20px; align-items: start; }
    .card { border: 1px solid #d8cfbd; border-radius: 22px; padding: 18px; background: rgba(255, 250, 240, 0.82); box-shadow: 0 20px 50px rgba(97, 63, 21, 0.12); }
    label { display: block; margin: 12px 0 6px; font-weight: 800; }
    input, textarea { width: 100%; box-sizing: border-box; border: 1px solid #d8cfbd; border-radius: 14px; padding: 10px 12px; font: inherit; background: #fffdf7; }
    textarea { min-height: 112px; resize: vertical; }
    button, .button { display: inline-block; border: 0; border-radius: 999px; padding: 10px 16px; color: white; background: #0f766e; font-weight: 800; text-decoration: none; cursor: pointer; }
    .row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-top: 14px; }
    .check { display: flex; gap: 8px; align-items: center; font-weight: 600; color: #445; }
    .check input { width: auto; }
    pre { max-height: 620px; overflow: auto; white-space: pre-wrap; word-break: break-word; color: #f8fafc; background: #111827; border-radius: 16px; padding: 14px; font-size: 12px; line-height: 1.45; }
    .error { color: #991b1b; background: #fee2e2; border-radius: 12px; padding: 10px; }
    .status { color: #164e63; background: #e0f2fe; border-radius: 12px; padding: 10px; margin: 10px 0; }
    .hint { color: #675c4b; background: #fff7d6; border-radius: 12px; padding: 10px; font-size: 13px; line-height: 1.6; }
    .artifact { color: #102a24; background: #eaf7f3; border: 1px solid #b9ded3; border-radius: 16px; padding: 14px; white-space: pre-wrap; }
    .meta { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 12px 0; }
    .pill { border-radius: 14px; padding: 10px; background: #fff7d6; color: #4b3d20; font-size: 13px; }
    .shots { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin: 10px 0 18px; }
    .shots img { width: 100%; border: 1px solid #d8cfbd; border-radius: 14px; background: white; box-shadow: 0 10px 26px rgba(55, 40, 15, 0.14); }
    @media (max-width: 820px) { .grid { grid-template-columns: 1fr; } .meta { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main>
    <h1>Python Browser Agent</h1>
    <p class="subtitle">Python-only: Playwright 浏览器控制 + OpenAI-compatible LLM Planner + 规则回退 + 安全拦截。</p>
    <div class="grid">
      <section class="card">
        <form method="post">
          <label for="url">URL</label>
          <input id="url" name="url" value="{{ form.url }}">
          <label for="task">任务</label>
          <textarea id="task" name="task">{{ form.task }}</textarea>
          <label for="api_base">API Base</label>
          <input id="api_base" name="api_base" value="{{ form.api_base }}">
          <label for="model">Model</label>
          <input id="model" name="model" value="{{ form.model }}" placeholder="gpt-4o-mini / qwen-vl-plus / ...">
          <label for="api_key">API Key</label>
          <input id="api_key" name="api_key" value="" type="password" placeholder="{% if form.api_key_configured %}已配置；留空使用环境变量{% else %}留空则使用规则 Planner{% endif %}">
          <label for="cdp_url">Chrome CDP URL（可选，用于操控已打开的 Chrome）</label>
          <input id="cdp_url" name="cdp_url" value="{{ form.cdp_url }}" placeholder="http://127.0.0.1:9222">
          <div class="status">{{ cdp_status }}</div>
          <div class="hint">若未检测到 CDP，可先运行：python3 scripts/launch_chrome_cdp.py --url http://127.0.0.1:8765</div>
          <label for="max_steps">最大动作步数</label>
          <input id="max_steps" name="max_steps" value="{{ form.max_steps }}" inputmode="numeric">
          <label for="screenshot_dir">截图目录</label>
          <input id="screenshot_dir" name="screenshot_dir" value="{{ form.screenshot_dir }}">
          <label for="slow_mo">可视化慢动作（毫秒）</label>
          <input id="slow_mo" name="slow_mo" value="{{ form.slow_mo }}" inputmode="numeric">
          <label for="linger">临时浏览器运行后停留秒数</label>
          <input id="linger" name="linger" value="{{ form.linger }}" inputmode="decimal">
          <div class="row">
            <label class="check"><input type="checkbox" name="headless" {% if form.headless %}checked{% endif %}> Headless</label>
            <label class="check"><input type="checkbox" name="allow_explicit_submit" {% if form.allow_explicit_submit %}checked{% endif %}> 允许显式提交/发送</label>
            <button type="submit">运行 Agent</button>
            {% if result %}<a class="button" href="/download/trajectory.json">导出 trajectory.json</a>{% endif %}
          </div>
        </form>
      </section>
      <section class="card">
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        {% if result %}
          <h2>Artifact</h2>
          <div class="artifact">{{ result.execution.artifact }}</div>
          <div class="meta">
            <div class="pill">浏览器模式：{{ result.browserMode }}</div>
            <div class="pill">连接状态：{{ result.connectionStatus }}</div>
            <div class="pill">最终 URL：{{ result.execution.url }}</div>
          </div>
          {% if screenshots %}
            <h2>Observation Screenshots</h2>
            <div class="shots">
              {% for shot in screenshots %}
                <a href="/artifact/screenshot?path={{ quote(shot) }}" target="_blank"><img src="/artifact/screenshot?path={{ quote(shot) }}" alt="{{ shot }}"></a>
              {% endfor %}
            </div>
          {% endif %}
          <h2>Trajectory</h2>
          <pre>{{ pretty(result) }}</pre>
        {% else %}
          <p>输入 URL 和任务后运行。未填 API Key 时自动使用规则 Planner。</p>
        {% endif %}
      </section>
    </div>
  </main>
</body>
</html>
"""
