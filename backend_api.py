from __future__ import annotations

import json
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from browser_agent.config import build_agent_config
from browser_agent.harness.runtime import HarnessRuntime
from browser_agent.output.markdown import render_markdown_report
from browser_agent.types import Observation

HOST = "127.0.0.1"
PORT = 8000


def _normalized_text(value) -> str:
    return " ".join(str(value or "").split()).strip()


def _control_role(control: dict) -> str:
    role = _normalized_text(control.get("role")).lower()
    if role:
        return role
    tag = _normalized_text(control.get("tag")).lower()
    input_type = _normalized_text(control.get("type")).lower()
    if tag == "textarea":
        return "textbox"
    if tag == "button":
        return "button"
    if tag == "input":
        if input_type == "search":
            return "searchbox"
        if input_type in {"button", "submit", "reset"}:
            return "button"
        if input_type in {"checkbox", "radio"}:
            return input_type
        return "textbox"
    return tag or "control"


def _control_element(control: dict) -> dict:
    element_id = control.get("index")
    label = _normalized_text(control.get("label"))
    role = _control_role(control)
    tag = _normalized_text(control.get("tag")).lower()
    input_type = _normalized_text(control.get("type")).lower()
    return {
        "element_id": element_id,
        "id": element_id,
        "tag": tag,
        "type": input_type,
        "role": role,
        "name": label,
        "label": label,
        "text": label,
        "visible": bool(control.get("visible", True)),
        "disabled": bool(control.get("disabled", False)),
        "source": "current_page_control",
    }


def _link_element(link: dict, fallback_id: str) -> dict:
    text = _normalized_text(link.get("text"))
    href = _normalized_text(link.get("href") or link.get("url"))
    return {
        "element_id": fallback_id,
        "id": fallback_id,
        "tag": "a",
        "role": "link",
        "name": text,
        "label": text,
        "text": text,
        "href": href,
        "url": href,
        "visible": True,
        "disabled": False,
        "source": "current_page_link",
    }


def _observation_from_payload(current_page_payload: dict, start_url: str) -> Observation:
    links = current_page_payload.get("links") if isinstance(current_page_payload.get("links"), list) else []
    controls = current_page_payload.get("controls") if isinstance(current_page_payload.get("controls"), list) else []

    elements = []
    form_fields = []
    visible_buttons = []
    accessibility_tree = []

    for index, link in enumerate(links):
        if not isinstance(link, dict):
            continue
        href = _normalized_text(link.get("href") or link.get("url"))
        if not href:
            continue
        elements.append(_link_element(link, fallback_id=f"link-{index}"))

    for control in controls:
        if not isinstance(control, dict):
            continue
        if control.get("visible") is False or control.get("disabled") is True:
            continue
        element = _control_element(control)
        elements.append(element)
        accessibility_tree.append(element)
        role = str(element.get("role") or "")
        if role in {"searchbox", "textbox", "combobox", "checkbox", "radio", "select"}:
            form_fields.append(element)
        if role == "button":
            visible_buttons.append(element)

    return Observation(
        url=str(current_page_payload.get("url") or start_url),
        title=str(current_page_payload.get("title") or ""),
        text=str(current_page_payload.get("text") or ""),
        elements=elements,
        accessibility_tree=accessibility_tree,
        form_fields=form_fields,
        visible_buttons=visible_buttons,
        visual_summary=_normalized_text(current_page_payload.get("visual_summary") or ""),
        extracted_fields={
            "resume_from_current_page": True,
            "control_count": len(accessibility_tree),
            "link_count": len([item for item in elements if item.get("role") == "link"]),
        },
    )


def run_workflow(payload: dict) -> dict:
    goal = payload.get("goal", "")
    if not goal:
        raise ValueError("goal is required")

    start_url = payload.get("url", "https://example.com")
    domain = payload.get("domain", "auto")
    max_steps = int(payload.get("max_steps", 8))
    headed = bool(payload.get("headed", False))
    current_page_payload = payload.get("current_page_observation") if isinstance(payload.get("current_page_observation"), dict) else None

    agent_config = build_agent_config(
        provider=payload.get("provider"),
        model=payload.get("model"),
        api_key_env=payload.get("api_key_env"),
        api_base_url=payload.get("api_base_url"),
        use_llm=bool(payload.get("use_llm", False)),
        vision_provider=payload.get("vision_provider"),
        vision_model=payload.get("vision_model"),
        vision_api_key_env=payload.get("vision_api_key_env"),
        vision_api_base_url=payload.get("vision_api_base_url"),
    )

    runtime = HarnessRuntime(max_steps=max_steps, headless=not headed, agent_config=agent_config)
    initial_observation = None
    if current_page_payload:
        initial_observation = _observation_from_payload(current_page_payload, start_url)
    result = runtime.run(goal=goal, start_url=start_url, domain=domain, initial_observation=initial_observation)

    out_dir = Path("runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest-run.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "latest-report.md").write_text(render_markdown_report(result), encoding="utf-8")
    result["markdown_report_path"] = str(out_dir / "latest-report.md")
    return result


def safe_config_payload() -> dict:
    config = build_agent_config(use_llm=True)
    return {
        "ok": True,
        "provider": config.provider,
        "model": config.model,
        "api_base_url": config.api_base_url,
        "api_key_configured": config.api_key_configured,
        "vision_provider": config.vision_provider,
        "vision_model": config.vision_model,
        "vision_api_base_url": config.vision_api_base_url,
        "vision_api_key_configured": bool(config.vision_api_key_value),
        "llm_timeout_sec": config.llm_timeout_sec,
        "vision_timeout_sec": config.vision_timeout_sec,
        "planner_max_tokens": config.planner_max_tokens,
        "report_max_tokens": config.report_max_tokens,
        "report_retry_max_tokens": config.report_retry_max_tokens,
        "use_multimodal_planning": config.use_multimodal_planning,
        "use_visual_precheck": config.use_visual_precheck,
    }


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, body: dict) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._json(200, {"ok": True})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/health":
            self._json(200, {"ok": True, "service": "browser-agent-backend"})
            return
        if self.path == "/api/config":
            self._json(200, safe_config_payload())
            return
        if self.path == "/api/latest":
            fp = Path("runs/latest-run.json")
            if not fp.exists():
                self._json(404, {"ok": False, "error": "latest-run.json not found"})
                return
            self._json(200, {"ok": True, "result": json.loads(fp.read_text(encoding="utf-8"))})
            return
        if self.path == "/api/latest-report":
            fp = Path("runs/latest-report.md")
            if not fp.exists():
                self._json(404, {"ok": False, "error": "latest-report.md not found"})
                return
            self.send_response(200)
            data = fp.read_text(encoding="utf-8").encode("utf-8")
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/run":
            self._json(404, {"ok": False, "error": "not found"})
            return

        try:
            content_len = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_len)
            payload = json.loads(raw.decode("utf-8") or "{}")
            result = run_workflow(payload)
            self._json(200, {"ok": True, "result": result})
        except Exception as exc:  # pylint: disable=broad-except
            self._json(500, {"ok": False, "error": str(exc), "traceback": traceback.format_exc()})


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Backend API listening on http://{HOST}:{PORT}")
    server.serve_forever()
