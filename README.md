# Browser Copilot Agent (Harness Runtime)

Browser Copilot Agent is a harness-first browser agent project:

`LLM + Browser Harness + Memory + Verification + Self-evolution`

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py --goal "帮我比较三款耳机并推荐"
```

## Project Layout

```text
browser_agent/
  planner/
  browser/
  harness/
  memory/
  verifier/
  vision/
  evaluation/
docs/
app.py
```

## Notes

- This is the rebuilt skeleton after full reset.
- Runtime is harness-first, with deterministic fallback behavior.
