#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_py.web_app import run_app


if __name__ == "__main__":
    run_app(host="127.0.0.1", port=8787, debug=False)
