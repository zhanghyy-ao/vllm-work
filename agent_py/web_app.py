from __future__ import annotations

import html
import json
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .comparison import recommend_from_observation
from .llm_planner import LLMConfig
from .llm_planner import try_plan_with_llm
from .memory import AgentMemory
from .planner import plan_task
from .runner import BrowserAgentRunner, save_trajectory
from .safety import sanitize_plan
from .schema import Element, Observation
from .workflow import build_workflow_controller


LAST_RESULT: Dict[str, Any] = {}


def create_app():
    """Create Flask app for extension APIs and local demo UI."""
    try:
        from flask import Flask, Response, abort, jsonify, redirect, render_template_string, request, send_file, url_for
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Flask is not installed. Run: python3 -m pip install -r requirements.txt") from exc

    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    @app.route("/api/extension/health", methods=["GET", "OPTIONS"])
    def extension_health():
        if request.method == "OPTIONS":
            return Response(status=204)
        env_config = LLMConfig.from_env()
        return jsonify(
            {
                "ok": True,
                "service": "python-browser-agent",
                "version": "0.1.0",
                "llmEnvConfigured": env_config.enabled,
                "llmDefaultSource": "python-llm" if env_config.enabled else "python-rule",
                "llmModel": env_config.model if env_config.enabled else "",
                "llmTransport": env_config.transport if env_config.enabled else "",
            }
        )

    @app.route("/api/extension/plan", methods=["POST", "OPTIONS"])
    def extension_plan():
        """Build a plan from observation; recommendation tasks may enforce LLM-only planning."""
        if request.method == "OPTIONS":
            return Response(status=204)
        payload = request.get_json(silent=True) or {}
        task = str(payload.get("task") or "").strip()
        observation_data = payload.get("observation") if isinstance(payload.get("observation"), dict) else {}
        settings = payload.get("settings") if isinstance(payload.get("settings"), dict) else {}
        if not task:
            return jsonify({"ok": False, "error": "task is required"}), 400
        observation = _observation_from_extension(observation_data)
        task_mode = _task_mode(task)
        llm_required = task_mode == "recommendation"
        env_config = LLMConfig.from_env()
        # Extension defaults to backend-managed LLM config from .env.
        # We only honor override fields if explicitly enabled for debugging.
        allow_override = bool(settings.get("allowLlmOverride"))
        llm_config = LLMConfig(
            api_base=str(settings.get("apiBase") or env_config.api_base) if allow_override else env_config.api_base,
            api_key=str(settings.get("apiKey") or env_config.api_key) if allow_override else env_config.api_key,
            model=str(settings.get("model") or env_config.model) if allow_override else env_config.model,
        )
        allow_explicit_submit = bool(settings.get("allowExplicitSubmit"))
        source = "rule"
        warnings = []
        llm_status = "not_requested"
        failure_code = ""
        explicit_use_llm = settings.get("useLlm")
        llm_requested = bool(explicit_use_llm) if explicit_use_llm is not None else llm_config.enabled
        if llm_required:
            llm_requested = True
        llm_plan = None
        if llm_requested:
            try:
                llm_plan = try_plan_with_llm(task, observation, llm_config, allow_explicit_submit=allow_explicit_submit)
                llm_status = "success" if llm_plan else "empty"
            except Exception as exc:
                warnings.append(f"vLLM 规划失败，已回退规则 planner：{exc}")
                llm_status = "failed"
                failure_code = _llm_failure_code(str(exc))
        if llm_required and (not llm_requested or not llm_plan):
            if llm_status == "not_requested":
                llm_status = "failed"
                failure_code = "task_failed_llm_required"
            elif not failure_code:
                failure_code = "task_failed_llm_required"
            return jsonify(
                {
                    "ok": False,
                    "source": "none",
                    "taskMode": task_mode,
                    "llmRequired": True,
                    "llmRequested": llm_requested,
                    "llmEnabled": llm_config.enabled,
                    "llmModel": llm_config.model if llm_config.enabled else "",
                    "llmTransport": llm_config.transport if llm_config.enabled else "",
                    "llmStatus": llm_status,
                    "failureCode": failure_code,
                    "warnings": warnings or ["推荐任务要求 LLM 参与，当前规划已中断。"],
                    "error": "LLM required for recommendation task.",
                }
            ), 409
        if llm_plan:
            plan = llm_plan
            source = "python-llm"
        else:
            plan = sanitize_plan(plan_task(task, observation), observation, allow_explicit_submit=allow_explicit_submit)
            plan = BrowserAgentRunner()._complete_plan(task, plan)
            source = "python-rule"
        controller = build_workflow_controller(task, observation, plan, source)
        return jsonify(
            {
                "ok": True,
                "source": source,
                "taskMode": task_mode,
                "llmRequired": llm_required,
                "llmRequested": llm_requested,
                "llmEnabled": llm_config.enabled,
                "llmModel": llm_config.model if llm_config.enabled else "",
                "llmTransport": llm_config.transport if llm_config.enabled else "",
                "llmStatus": llm_status,
                "failureCode": failure_code,
                "warnings": warnings + list(plan.warnings),
                "plan": plan.to_dict(),
                "controller": controller.to_dict(),
            }
        )

    @app.route("/api/extension/recommend", methods=["POST", "OPTIONS"])
    def extension_recommend():
        """Persist recommendation payload to JSON and produce LLM-based comparison result."""
        if request.method == "OPTIONS":
            return Response(status=204)
        payload = request.get_json(silent=True) or {}
        task = str(payload.get("task") or "").strip()
        observation_data = payload.get("observation") if isinstance(payload.get("observation"), dict) else {}
        execution_data = payload.get("execution") if isinstance(payload.get("execution"), dict) else {}
        settings = payload.get("settings") if isinstance(payload.get("settings"), dict) else {}
        if not task:
            return jsonify({"ok": False, "error": "task is required"}), 400

        observation = _observation_from_extension(observation_data)
        env_config = LLMConfig.from_env()
        allow_override = bool(settings.get("allowLlmOverride"))
        llm_config = LLMConfig(
            api_base=str(settings.get("apiBase") or env_config.api_base) if allow_override else env_config.api_base,
            api_key=str(settings.get("apiKey") or env_config.api_key) if allow_override else env_config.api_key,
            model=str(settings.get("model") or env_config.model) if allow_override else env_config.model,
        )

        memory = AgentMemory(task=task)
        raw_memory = payload.get("memory") if isinstance(payload.get("memory"), dict) else {}
        memory.search_queries = [str(item) for item in raw_memory.get("searchQueries", [])] if isinstance(raw_memory.get("searchQueries"), list) else []
        memory.visited_urls = [str(item) for item in raw_memory.get("visitedUrls", [])] if isinstance(raw_memory.get("visitedUrls"), list) else []
        memory.notes = [str(item) for item in raw_memory.get("notes", [])] if isinstance(raw_memory.get("notes"), list) else []
        memory.candidate_snapshots = [item for item in raw_memory.get("candidateSnapshots", []) if isinstance(item, dict)] if isinstance(raw_memory.get("candidateSnapshots"), list) else []
        memory.detail_pages = [item for item in raw_memory.get("detailPages", []) if isinstance(item, dict)] if isinstance(raw_memory.get("detailPages"), list) else []

        artifact_path = _persist_recommendation_payload(task, observation_data, execution_data, raw_memory)
        result = recommend_from_observation(task, observation, memory=memory, llm_config=llm_config, require_llm=True)
        if not result.get("ok"):
            return jsonify(
                {
                    "ok": False,
                    "error": result.get("error") or "recommendation_failed",
                    "message": result.get("message") or "推荐任务失败",
                    "artifactPath": str(artifact_path),
                    "llmRequired": True,
                    "llmEnabled": llm_config.enabled,
                    "llmModel": llm_config.model if llm_config.enabled else "",
                    "llmTransport": llm_config.transport if llm_config.enabled else "",
                }
            ), 409
        return jsonify(
            {
                "ok": True,
                "artifactPath": str(artifact_path),
                "source": result.get("source", "python-llm"),
                "llmRequired": True,
                "llmEnabled": llm_config.enabled,
                "llmModel": llm_config.model if llm_config.enabled else "",
                "llmTransport": llm_config.transport if llm_config.enabled else "",
                "recommendation": result,
            }
        )

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


def _observation_from_extension(data: Dict[str, Any]) -> Observation:
    elements = []
    for item in data.get("elements", []) if isinstance(data.get("elements"), list) else []:
        if not isinstance(item, dict):
            continue
        elements.append(
            Element(
                id=str(item.get("id") or ""),
                tag=str(item.get("tag") or ""),
                selector=str(item.get("selector") or ""),
                role=str(item.get("role") or ""),
                type=str(item.get("type") or ""),
                name=str(item.get("name") or ""),
                label=str(item.get("label") or ""),
                text=str(item.get("text") or ""),
                placeholder=str(item.get("placeholder") or ""),
                href=str(item.get("href") or ""),
                value=str(item.get("value") or ""),
                form_id=str(item.get("formId") or item.get("form_id") or ""),
                section_label=str(item.get("sectionLabel") or item.get("section_label") or ""),
                visible=bool(item.get("visible", True)),
                enabled=bool(item.get("enabled", True)),
                bbox={key: float(value) for key, value in dict(item.get("bbox") or {}).items()},
                content_editable=bool(item.get("contentEditable", False)),
                clickable=bool(item.get("clickable", False)),
            )
        )
    return Observation(
        url=str(data.get("url") or ""),
        title=str(data.get("title") or ""),
        text=str(data.get("text") or ""),
        elements=elements,
        cards=[item for item in data.get("cards", []) if isinstance(item, dict)][:20] if isinstance(data.get("cards"), list) else [],
        tables=[item for item in data.get("tables", []) if isinstance(item, list)][:6] if isinstance(data.get("tables"), list) else [],
        links=[item for item in data.get("links", []) if isinstance(item, dict)][:40] if isinstance(data.get("links"), list) else [],
        emails=[str(item) for item in data.get("emails", [])][:20] if isinstance(data.get("emails"), list) else [],
        prices=[str(item) for item in data.get("prices", [])][:20] if isinstance(data.get("prices"), list) else [],
        headings=[str(item) for item in data.get("headings", [])][:20] if isinstance(data.get("headings"), list) else [],
    )


def _task_mode(task: str) -> str:
    return "recommendation" if _is_recommendation_task(task) else "general"


def _is_recommendation_task(task: str) -> bool:
    text = str(task or "")
    return bool(
        __import__("re").search(
            r"推荐|对比|比较|性价比|耳机|手机|笔记本|电脑|camera|headphone|recommend|compare|rank",
            text,
            __import__("re").I,
        )
    )


def _llm_failure_code(error_text: str) -> str:
    lowered = str(error_text or "").lower()
    if "timeout" in lowered:
        return "llm_timeout"
    if "invalid_grant" in lowered:
        return "llm_invalid_grant"
    if "auth_unavailable" in lowered:
        return "llm_provider_unavailable"
    if "model_not_found" in lowered:
        return "llm_model_not_found"
    return "task_failed_llm_required"


def _persist_recommendation_payload(task: str, observation: Dict[str, Any], execution: Dict[str, Any], memory: Dict[str, Any]) -> Path:
    base = Path.cwd() / "runs" / "recommendation"
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = base / f"recommend-{stamp}.json"
    payload = {
        "task": task,
        "savedAt": datetime.now().isoformat(),
        "observation": observation if isinstance(observation, dict) else {},
        "execution": execution if isinstance(execution, dict) else {},
        "memory": memory if isinstance(memory, dict) else {},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


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
          {% if result.workflow %}
            <h2>Workflow</h2>
            <pre>{{ pretty(result.workflow) }}</pre>
          {% endif %}
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
