from __future__ import annotations

import json
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from browser_agent.config import build_agent_config
from browser_agent.harness.runtime import HarnessRuntime
from browser_agent.output.markdown import render_markdown_report

HOST = "127.0.0.1"
PORT = 8000


def run_workflow(payload: dict) -> dict:
    goal = payload.get("goal", "")
    if not goal:
        raise ValueError("goal is required")

    start_url = payload.get("url", "https://example.com")
    domain = payload.get("domain", "auto")
    max_steps = int(payload.get("max_steps", 8))
    headed = bool(payload.get("headed", False))

    agent_config = build_agent_config(
        provider=payload.get("provider"),
        model=payload.get("model"),
        api_key_env=payload.get("api_key_env"),
        api_base_url=payload.get("api_base_url"),
        use_llm=bool(payload.get("use_llm", False)),
        vision_provider=payload.get("vision_provider"),
        vision_model=payload.get("vision_model"),
        vision_api_key_env=payload.get("vision_api_key_env"),
    )

    runtime = HarnessRuntime(max_steps=max_steps, headless=not headed, agent_config=agent_config)
    result = runtime.run(goal=goal, start_url=start_url, domain=domain)

    out_dir = Path("runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest-run.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "latest-report.md").write_text(render_markdown_report(result), encoding="utf-8")
    result["markdown_report_path"] = str(out_dir / "latest-report.md")
    return result


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
