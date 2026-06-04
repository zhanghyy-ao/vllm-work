# Browser Workflow Automation Platform

Browser Workflow Automation Platform is a harness-first browser agent MVP:

`Goal -> WorkflowSpec -> Browser Execution -> Verification -> Evidence -> Report`

With LLM enabled, the effective runtime loop is:

```text
Goal -> Evidence Checklist -> Observe Page -> LLM Next Action -> Browser Execute -> Verify -> Memory -> Repeat/Stop -> Report
```

The first runnable version can run with an OpenAI-compatible multimodal model as the LLM agent. When `--use-llm` and a valid API key are configured, the runtime uses an observation-driven agent loop: observe the current page, ask the LLM to choose the next safe browser action, execute it, verify progress, update memory, and repeat. Research workflows no longer carry fixed action templates; without an enabled LLM, they produce a workflow shell and do not run browser actions.

Browser Copilot Agent is a harness-first browser agent project:
`LLM + Browser Harness + Memory + Verification + Self-evolution`

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
cp .env.example .env
python3 app.py --goal "帮我比较三款耳机并推荐"

python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py --goal "帮我比较三款耳机并推荐"
```

## Demos

```bash
python3 app.py \
  --domain github \
  --goal "帮我找多模态OOD相关开源项目" \
  --url "https://github.com"

python3 app.py \
  --domain paper \
  --goal "找最近 Agent hallucination 的论文" \
  --url "https://arxiv.org"
```

Use `--headed` if you want to watch the browser window during execution.

## Agent/API Config

The default LLM provider is an OpenAI-compatible endpoint. Put the real key in `.env` or export it in your shell; do not commit secrets.

Config can come from `.env`, shell environment, or CLI flags:

```bash
python3 app.py \
  --domain github \
  --goal "帮我找多模态OOD相关开源项目" \
  --provider openai_compatible \
  --model gpt-5.5 \
  --api-key-env BROWSER_AGENT_API_KEY \
  --api-base-url https://synai996.space/v1 \
  --use-llm
```

Relevant environment variables:

```text
BROWSER_AGENT_NAME
BROWSER_AGENT_PROVIDER
BROWSER_AGENT_MODEL
BROWSER_AGENT_MODEL_FALLBACKS
BROWSER_AGENT_API_BASE_URL
BROWSER_AGENT_API_KEY_ENV
BROWSER_AGENT_USE_LLM
BROWSER_AGENT_API_KEY
BROWSER_AGENT_VISION_PROVIDER
BROWSER_AGENT_VISION_MODEL
BROWSER_AGENT_VISION_MODEL_FALLBACKS
BROWSER_AGENT_VISION_API_BASE_URL
BROWSER_AGENT_VISION_API_KEY_ENV
BROWSER_AGENT_HTTP_USER_AGENT
BROWSER_AGENT_LLM_TIMEOUT_SEC
BROWSER_AGENT_VISION_TIMEOUT_SEC
BROWSER_AGENT_PLANNER_MAX_TOKENS
BROWSER_AGENT_REPORT_MAX_TOKENS
BROWSER_AGENT_REPORT_RETRY_MAX_TOKENS
BROWSER_AGENT_USE_MULTIMODAL_PLANNING
BROWSER_AGENT_USE_VISUAL_PRECHECK
```

Multimodal planning sends the current screenshot to the same OpenAI-compatible model whenever a screenshot is available:

```bash
python3 app.py \
  --domain shopping \
  --goal "预算1000元以内，推荐一款适合通勤和办公室使用的降噪耳机" \
  --url "https://www.bing.com" \
  --max-steps 8 \
  --use-llm \
  --provider openai_compatible \
  --model gpt-5.5 \
  --api-key-env BROWSER_AGENT_API_KEY \
  --api-base-url https://synai996.space/v1 \
  --vision-provider openai_compatible \
  --vision-model gpt-5.5 \
  --vision-api-key-env BROWSER_AGENT_API_KEY \
  --vision-api-base-url https://synai996.space/v1
```

## Output

Each run writes the latest structured result to:

```text
runs/latest-run.json
```

Each run also writes a human-readable Markdown report to `runs/latest-report.md`; the backend serves it from `GET /api/latest-report`.

The result includes:

- `workflow`: generated workflow spec and nodes
- `steps`: execution results and fallback information
- `memory.evidence`: source-bound evidence items
- `report`: summary, candidates, recommendations, decision criteria, comparison matrix, video digest, uncertainties, and next actions
- `events`: trace records for observability
- `metrics`: step accuracy plus task-level checklist coverage, final-answer grounding, citation correctness, and browser-state goal matching

## Agent Loop Capabilities

The dynamic browser agent now observes more than URL/title/body text. Each browser step can attach:

- interactable elements with `element_id`, role/name/text, selector, and bounding box
- form fields, visible buttons, and a compact accessibility-style tree
- screenshot path and optional multimodal visual summary
- recent action history, failed actions, visited URLs, and repeated-query warnings

The LLM can choose safe low-level browser actions:

```text
goto, search_web, collect_links, open_candidate, deep_read_candidates,
extract_page, extract_video, summarize_text, click_element, type_text,
select_option, scroll, wait, back, press_key, stop
```

Dynamic safety policy blocks purchase/payment/login/destructive actions and avoids repeating identical actions or searches.

## Smarter Research And Video Tasks

GitHub repository tasks now normalize browser-agent goals into source-friendly search queries and deep-read candidate repositories through the GitHub API. Reports can include stars, forks, language, license, update time, topics, and README excerpts for open-source project comparison.
Reports now score comparison rows by domain-specific evidence and generate ranked recommendations with `score` and `score_reasons`, so users can see why a repo/product/video was recommended.


With `--use-llm`, the planner now builds a visible research strategy instead of a single generic query, then the runtime uses the strategy as a checklist rather than a fixed script. The LLM receives current page state, candidate links, recent traces, memory evidence, available safe actions, and the evidence checklist each round, and chooses the next action dynamically.

Example:

```bash
python3 app.py \
  --domain shopping \
  --goal "预算1000元以内，推荐一款适合通勤和办公室使用的降噪耳机，要比较品牌、类型、价格、音质、降噪、佩戴舒适度和用户评价" \
  --url "https://www.bing.com" \
  --max-steps 10 \
  --use-llm
```

Video tasks use `extract_video` to collect page metadata, visible transcript/description text, candidate video links, screenshots, YouTube oEmbed data, optional `yt-dlp` metadata, and optional key-frame extraction when `yt-dlp` plus `ffmpeg` are installed. Multimodal visual analysis supports Gemini or OpenAI-compatible vision models for screenshot/key-frame understanding, and safely reports an unavailable state when keys or media tools are missing.

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

## Checks

```bash
python3 -m compileall browser_agent app.py
```

## Docs

- [Feature spec](docs/mvp-browser-research-copilot/03-feature-spec.md)
- [Code walkthrough](docs/mvp-browser-research-copilot/04-code-walkthrough.md)
- [GitHub references and multimodal roadmap](docs/github-references-and-multimodal-roadmap.md)

## Regression Checks

Run the full lightweight regression suite with:

```bash
tests/run_checks.sh
```

It covers Python compile checks, Chrome extension syntax/manifest checks, monitor scoring for shopping/video/browser tasks, backend relevance filters, and Gemini's no-key fallback behavior.

The Chrome extension popup renders structured cards for summaries, visible planning, recommendations, comparison evidence, video digest, multimodal status, and monitor traces instead of raw JSON.
The extension monitor can also derive safe page actions from live browser state, such as filling visible search boxes or opening verified candidate links, before falling back to URL navigation.

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
