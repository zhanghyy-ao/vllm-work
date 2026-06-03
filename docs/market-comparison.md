# Market Comparison

This homework project now compares itself against mainstream browser-agent products and implements explicit advantages in code.

## Compared products

- OpenAI Operator / ChatGPT agent
- Anthropic computer use
- Browser Use
- Google Project Mariner

## What this project does better for a homework demo

1. It has explicit scenario templates.
   Market products are strong general agents, but they do not expose a local scenario registry with deterministic grading artifacts.

2. It pauses sensitive actions for approval.
   Reservation-style actions now stop at a handoff point unless `--auto-approve-sensitive` is provided.

3. It emits audit-ready outputs.
   Every run includes plan metadata, step logs, memory traces, evidence summary, and metrics in `runs/latest-run.json`.

4. It includes a built-in benchmark view.
   Each run can attach a `market_comparison` block showing where this harness leads on explainability, verification, and regression testing.

## Surpass strategy

This project does not try to beat consumer products on raw web breadth. It beats them on:

- explainability
- grading friendliness
- safety handoff
- deterministic regression testing
- reusable scenario templates

That is the right tradeoff for a course assignment and an engineering demo.

## Relevant entry points

- Planner: `browser_agent/planner/tot.py`
- Runtime: `browser_agent/harness/runtime.py`
- Market scoring: `browser_agent/market/compare.py`
- Tests: `tests/test_runtime.py`

## Source references

- OpenAI Operator, published January 23, 2025:
  `https://openai.com/index/introducing-operator/`
- Anthropic computer use, published October 22, 2024:
  `https://www.anthropic.com/news/3-5-models-and-computer-use`
- Browser Use official docs:
  `https://docs.browser-use.com/`
- Google Project Mariner:
  `https://deepmind.google/technologies/project-mariner/`
