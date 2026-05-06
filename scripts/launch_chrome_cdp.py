#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Optional


DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch Chrome with remote debugging for the Python Browser Agent.")
    parser.add_argument("--port", type=int, default=9222, help="Remote debugging port")
    parser.add_argument("--profile-dir", default="/tmp/browser-agent-chrome", help="Isolated Chrome profile directory")
    parser.add_argument("--chrome", default=DEFAULT_CHROME, help="Path to Chrome executable. Falls back to Playwright Chromium if missing.")
    parser.add_argument("--url", default="about:blank", help="Initial URL")
    parser.add_argument("--headless", action="store_true", help="Launch headless Chrome/Chromium for automated checks")
    parser.add_argument("--wait", type=float, default=8.0, help="Seconds to wait for the CDP endpoint to become ready")
    args = parser.parse_args()

    profile = Path(args.profile_dir)
    profile.mkdir(parents=True, exist_ok=True)
    chrome = _resolve_chrome(args.chrome)
    if not chrome:
        raise SystemExit("Could not find Chrome. Install Google Chrome or run: python3 -m playwright install chromium")
    command = [
        chrome,
        f"--remote-debugging-port={args.port}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-default-apps",
    ]
    if args.headless:
        command.extend(["--headless=new", "--disable-gpu"])
    command.append(args.url)
    print("Launching Chrome CDP:")
    print(" ".join(shlex.quote(part) for part in command))
    print(f"CDP URL: http://127.0.0.1:{args.port}")
    subprocess.Popen(command)
    if _wait_for_cdp(args.port, args.wait):
        print("CDP endpoint is ready.")
    else:
        print("Chrome was launched, but the CDP endpoint did not respond before timeout.")


def _resolve_chrome(candidate: str) -> Optional[str]:
    if candidate and Path(candidate).exists():
        return candidate
    for path in [
        DEFAULT_CHROME,
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]:
        if Path(path).exists():
            return path
    try:
        from playwright.sync_api import sync_playwright

        playwright = sync_playwright().start()
        try:
            executable = playwright.chromium.executable_path
            return executable if executable and Path(executable).exists() else None
        finally:
            playwright.stop()
    except Exception:
        return None


def _wait_for_cdp(port: int, timeout: float) -> bool:
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/json/version"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                return response.status == 200
        except Exception:
            time.sleep(0.2)
    return False


if __name__ == "__main__":
    main()
