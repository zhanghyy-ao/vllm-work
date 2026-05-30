# Browser Workflow Automation Platform

Browser Workflow Automation Platform is a harness-first browser agent MVP:

`Goal -> WorkflowSpec -> Browser Execution -> Verification -> Evidence -> Report`

The first runnable version can run with DeepSeek as the LLM agent. When `--use-llm` and `DEEPSEEK_API_KEY` are configured, the LLM improves search planning and produces the final evidence-grounded report. Without a key, it falls back to deterministic workflow templates.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
cp .env.example .env
python3 app.py --goal "帮我比较三款耳机并推荐"
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

DeepSeek is the default LLM provider. Put the real key in `.env` or export it in your shell; do not commit secrets.

Config can come from `.env`, shell environment, or CLI flags:

```bash
python3 app.py \
  --domain github \
  --goal "帮我找多模态OOD相关开源项目" \
  --provider deepseek \
  --model deepseek-chat \
  --api-key-env DEEPSEEK_API_KEY \
  --api-base-url https://api.deepseek.com \
  --use-llm
```

Relevant environment variables:

```text
BROWSER_AGENT_NAME
BROWSER_AGENT_PROVIDER
BROWSER_AGENT_MODEL
BROWSER_AGENT_API_BASE_URL
BROWSER_AGENT_API_KEY_ENV
BROWSER_AGENT_USE_LLM
DEEPSEEK_API_KEY
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

## Smarter Research And Video Tasks

GitHub repository tasks now normalize browser-agent goals into source-friendly search queries and deep-read candidate repositories through the GitHub API. Reports can include stars, forks, language, license, update time, topics, and README excerpts for open-source project comparison.
Reports now score comparison rows by domain-specific evidence and generate ranked recommendations with `score` and `score_reasons`, so users can see why a repo/product/video was recommended.


With `--use-llm`, the planner now builds a visible research strategy instead of a single generic query. For comparison and recommendation tasks, it returns decision criteria, subquestions, and multiple targeted searches.

Example:

```bash
python3 app.py \
  --domain shopping \
  --goal "预算1000元以内，推荐一款适合通勤和办公室使用的降噪耳机，要比较品牌、类型、价格、音质、降噪、佩戴舒适度和用户评价" \
  --url "https://www.bing.com" \
  --max-steps 10 \
  --use-llm
```

Video tasks use `extract_video` to collect page metadata, visible transcript/description text, candidate video links, screenshots, YouTube oEmbed data, optional `yt-dlp` metadata, and optional key-frame extraction when `yt-dlp` plus `ffmpeg` are installed. Gemini visual analysis is scaffolded through `GEMINI_API_KEY` for screenshot/key-frame understanding, and safely reports an unavailable state when keys or media tools are missing.

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
