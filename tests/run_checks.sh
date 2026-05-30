#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PWD}${PYTHONPATH:+:${PYTHONPATH}}"
python3 -m compileall browser_agent app.py backend_api.py
node --check chrome_extension/background.js
node --check chrome_extension/popup.js
python3 -m json.tool chrome_extension/manifest.json >/dev/null
node tests/chrome_monitor.test.js
node tests/popup_render.test.js
python3 tests/python_workflow_smoke.py
