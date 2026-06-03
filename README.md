# Browser Copilot Agent (Harness Runtime)

Browser Copilot Agent is a harness-first browser agent project:
`LLM + Browser Harness + Memory + Verification + Self-evolution`

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py --goal "帮我比较三款耳机并推荐"
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
tests/
app.py
```

## Built-in Scenarios

- Comparison and recommendation
- Form filling
- Web research
- Booking and reservation
- Lead collection
- Monitoring and alerts
- QA and regression checks

## Productized Strengths

- Scenario-aware planner with explicit routing and deliverables
- Sensitive action handoff before high-risk browser commits
- Evidence-rich run outputs with events, memory, verification, and metrics
- Built-in market comparison against mainstream browser-agent products
- Deterministic `unittest` coverage for homework demos and regressions

## Notes

- This repository keeps the original harness-first skeleton and extends it with four additional browser-control scenarios.
- Runtime behavior is deterministic so that homework demos and tests stay stable without a live browser session.
