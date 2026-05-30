# GitHub References And Multimodal Roadmap

Date: 2026-05-28

## Goal

Upgrade the current browser workflow agent from a single-query search tool into an intelligent browser assistant that can:

- plan deeper searches across multiple evidence dimensions;
- perform intelligent recommendation and comparison;
- assist browser work through observable page state and follow-up actions;
- search, read, and summarize video pages using metadata/text/transcript signals;
- reserve a Gemini multimodal path for screenshots, page visuals, and future video key-frame recognition.

## Referenced GitHub Implementations

### `browser-use/browser-use`

URL: <https://github.com/browser-use/browser-use>

Useful pattern:

- Keep real browser state as the source of truth.
- Put long-running control logic outside transient UI surfaces.
- Treat browser tools as composable actions: navigate, inspect, extract, decide, continue.

Applied here:

- Chrome extension background worker controls the active tab.
- Backend runtime uses `WorkflowNode` actions and verification events.
- Monitor loop observes the live page and continues when the task is not satisfied.

### `mendableai/firecrawl`

URL: <https://github.com/mendableai/firecrawl>

Useful pattern:

- Separate searching/crawling from structured extraction.
- Convert messy pages into clean evidence for downstream LLM summaries.

Applied here:

- Browser actions now distinguish `search_web`, `collect_links`, `extract_page`, `extract_video`, and `summarize_text`.
- Reports are grounded in `memory.evidence` instead of only the current page.

### `TencentCloudADP/youtu-agent`

URL: <https://github.com/TencentCloudADP/youtu-agent>

Useful pattern:

- Multi-step task decomposition and tool orchestration.
- Agent plans should include visible subgoals rather than a single generic query.

Applied here:

- `enhance_workflow_with_llm()` now asks for `reasoning_outline`, `decision_criteria`, `subquestions`, and `search_plan`.
- A recommendation task can expand into multiple targeted searches and extraction steps.

### Gemini Multimodal Examples

URL: <https://github.com/google-gemini/generative-ai-python>

Useful pattern:

- Use a multimodal model for screenshots, visual page grounding, and video key-frame understanding.

Applied here:

- Added `GeminiVisionProvider` as an optional provider.
- `extract_video` stores screenshots and declares `multimodal_ready` in the video digest.
- Without `GEMINI_API_KEY`, the pipeline remains fully functional and returns planned multimodal follow-up notes.

## Current Implementation

### Smarter Planning

LLM planning no longer returns only one search query. It now returns:

- `task_type`
- `reasoning_outline`
- `decision_criteria`
- `subquestions`
- `search_plan`

The runtime expands this into a larger workflow:

```text
goto -> search/query A -> collect A -> search/query B -> collect B -> ... -> summarize
```

For video tasks, the tail becomes:

```text
... -> extract_video -> summarize
```

### Recommendation And Comparison

Reports now include:

- `decision_criteria`
- `comparison_matrix`
- `recommendations`
- `uncertainties`
- `next_actions`

This supports tasks such as:

```text
预算1000元以内，推荐一款适合通勤和办公室使用的降噪耳机，要比较品牌、类型、价格、音质、降噪、佩戴舒适度和用户评价
```

### Video Reading

`extract_video` currently collects:

- page title;
- meta description/OpenGraph fields;
- visible page text;
- visible transcript/description/chapters when present;
- YouTube oEmbed metadata when applicable;
- optional `yt-dlp` metadata if `yt-dlp` is installed;
- screenshot path for future Gemini visual analysis;
- candidate video links from the page.

This gives a practical first version of video content organization before full key-frame extraction is added.

### Gemini Multimodal Path

`browser_agent/vision/multimodal.py` adds:

- `GeminiVisionProvider.analyze_image(image_path, prompt)`
- `build_video_visual_prompt(goal, known_context)`

Environment variables:

```text
BROWSER_AGENT_VISION_PROVIDER=gemini
BROWSER_AGENT_VISION_MODEL=gemini-1.5-flash
BROWSER_AGENT_VISION_API_KEY_ENV=GEMINI_API_KEY
GEMINI_API_KEY=
```

## Next Engineering Steps

1. Add candidate-page deep extraction so recommendations can open top links and read product/video/repo pages directly.
2. Add optional `yt-dlp` installation guidance and transcript normalization.
3. Add video key-frame sampling with `ffmpeg` or `yt-dlp` frame extraction.
4. Call Gemini on selected screenshots/key frames and merge visual findings into `multimodal_notes`.
5. Add browser-side task satisfaction scoring for shopping and video tasks, similar to the GitHub monitor.

## 2026-05-28 Follow-up Hardening

### Browser monitor domain scoring

The Chrome extension monitor now infers the active task domain and scores the live tab differently for GitHub, shopping, video, paper, and general tasks. This follows the `browser-use` idea that browser state should be the source of truth: a search result page is only an intermediate state for shopping/video tasks, not a completed task.

Implemented behavior:

- Shopping/recommendation tasks must land on a product, official, comparison, or review evidence page rather than a generic search page.
- Video tasks must land on a real video page such as YouTube, Bilibili, Vimeo, or a page with a video URL pattern.
- Follow-up URLs are collected from recommendations, candidates, source readings, comparison rows, and runtime events.
- The monitor can derive live follow-up URLs from the currently visible page links when the current page is insufficient.

### Video relevance and multimodal handoff

Video search now filters candidate links against task terms so unrelated videos are not opened simply because they appear first in Bing Videos. For CLIP/multimodal tutorial tasks, the deterministic fallback query is normalized to `CLIP 多模态 模型 入门 教程 视频 讲解`, and the extractor keeps a relevant Bilibili/YouTube candidate pool when the search page is noisy.

Runtime now attaches Gemini multimodal analysis to video reports when a screenshot exists:

- with `GEMINI_API_KEY`, `GeminiVisionProvider` analyzes the screenshot/key-frame handoff and stores the visual finding in `video_digest.visual_analysis` and `multimodal_notes`;
- without `GEMINI_API_KEY`, the report records a structured `unavailable` note instead of failing the workflow.

### Verification evidence

Commands run:

```bash
python3 -m py_compile browser_agent/browser/action.py browser_agent/planner/tot.py browser_agent/harness/runtime.py browser_agent/vision/multimodal.py
node --check chrome_extension/background.js
node --check chrome_extension/popup.js
python3 app.py --goal '帮我查找并整理一个 CLIP 多模态模型入门教程视频的主要内容' --domain video --url 'https://www.bing.com' --max-steps 6
```

The latest video run opened a relevant Bilibili CLIP tutorial page, extracted video metadata/text, captured a screenshot, and recorded Gemini multimodal handoff status. The run artifact is stored in `runs/latest-run-video.json`.

## 2026-05-28 Regression Harness

A lightweight regression harness was added so the browser-agent behavior can be verified without manually reopening Chrome each time.

### Added checks

- `tests/chrome_monitor.test.js` verifies the Chrome extension monitor logic:
  - shopping tasks reject search pages and accept real review/product evidence pages;
  - video tasks reject video search pages and accept real video pages;
  - follow-up URLs are gathered from recommendations, candidates, source readings, comparison rows, and live page links.
- `tests/python_workflow_smoke.py` verifies backend relevance filters and Gemini-safe fallback:
  - headphone review pages pass shopping relevance;
  - audio denoise utility pages are rejected for headphone shopping tasks;
  - CLIP tutorial video pages pass video relevance;
  - unrelated video pages are rejected;
  - Gemini vision reports a structured unavailable state when `GEMINI_API_KEY` is missing.
- `tests/run_checks.sh` runs compile checks, extension syntax checks, manifest JSON validation, and both regression suites.

### Latest end-to-end evidence

Commands run:

```bash
tests/run_checks.sh
python3 app.py --goal '预算1000元以内，推荐一款适合通勤和办公室使用的降噪耳机，要比较品牌、类型、价格、音质、降噪、佩戴舒适度和用户评价' --domain shopping --url 'https://www.bing.com' --max-steps 7
python3 app.py --goal '帮我查找并整理一个 CLIP 多模态模型入门教程视频的主要内容' --domain video --url 'https://www.bing.com' --max-steps 6
```

Results:

- shopping run: `ok=true`, 5 candidates, 5 deep-read source pages, stored in `runs/latest-run-shopping.json`;
- video run: `ok=true`, opened the Bilibili CLIP tutorial page, captured a screenshot, and recorded Gemini multimodal handoff notes, stored in `runs/latest-run-video.json`.

## 2026-05-28 Chrome Extension Report UI

The Chrome extension popup was upgraded from raw JSON output to a structured report view. This makes the browser assistant usable directly from Chrome after it controls and monitors the active tab.

Rendered sections:

- task summary and run metadata;
- visible planning outline and search plan;
- recommendations/candidates with source links;
- comparison evidence rows;
- video digest with source URL, transcript snippet, and screenshot path;
- Gemini/multimodal status;
- browser monitoring trace showing whether each observed page satisfied the task;
- uncertainties and next actions.

Regression coverage:

- `tests/popup_render.test.js` verifies that popup rendering includes shopping, video, multimodal, and monitor sections;
- the renderer is exported as a pure function for Node-based checks while still binding to Chrome DOM APIs inside the extension runtime;
- unsafe text is HTML-escaped before being inserted into the popup report.

## 2026-05-28 Optional Video Key-Frame Pipeline

The video workflow now includes an optional key-frame extraction layer for future Gemini visual understanding.

Implementation:

- `browser_agent/vision/keyframes.py` adds `extract_video_keyframes(url, out_root, max_frames)`.
- If `yt-dlp` and `ffmpeg` are installed, the extractor downloads a short initial clip and samples up to a small number of frames.
- If either tool is missing, the workflow records a structured unavailable status instead of failing.
- `extract_video` writes the key-frame status into `video_digest.keyframes`.
- The runtime combines `video_digest.screenshot_path` and any extracted key frames through `visual_inputs_from_video_digest()` before calling Gemini.
- With `GEMINI_API_KEY`, Gemini can analyze screenshots/key frames; without it, the report keeps a clear unavailable note.

Current environment evidence:

```text
yt-dlp not found
ffmpeg not found
ffprobe not found
```

End-to-end video verification still passes. The latest CLIP tutorial run opened `https://www.bilibili.com/video/BV1XZR9ByEV2/`, stored a screenshot, recorded `keyframes.reason=yt-dlp_not_installed`, and used the screenshot as the available visual input for Gemini handoff.

## 2026-05-28 Browser Page Action Layer

The Chrome extension monitor now has a small safe page-action layer, moving it closer to the browser-state/tool loop pattern used by browser automation agents.

Capabilities:

- `observeTab()` captures visible links plus visible, enabled controls such as inputs, textareas, buttons, and role=button elements.
- `derivePageActions()` can propose safe actions from the live page state:
  - `fill_and_submit` for visible search boxes;
  - `click_link` for verified candidate links such as GitHub repositories or video pages.
- `executePageAction()` performs only allowlisted actions. It does not execute arbitrary script strings from the model or backend.
- The monitor tries page actions before falling back to URL navigation, then observes the page again.
- The popup monitor trace now shows page actions and their result, so users can inspect what the browser assistant did.

Regression coverage:

- `tests/chrome_monitor.test.js` verifies search-box action planning and GitHub candidate link action planning.
- `tests/popup_render.test.js` verifies that page actions appear in the monitor report UI.

## 2026-05-28 GitHub Repository Deep Reading

GitHub project recommendation now uses structured repository evidence instead of only search-result snippets or rendered HTML.

Implementation:

- GitHub goals about browser automation/agents normalize Chinese task descriptions to the English query `browser automation agent LLM` before searching GitHub.
- `collect_links` falls back to a curated browser-agent reference seed list when GitHub search is too narrow or returns no repositories.
- `deep_read_candidates` uses the GitHub REST API for repository candidates:
  - repository full name and URL;
  - stars, forks, open issues;
  - primary language;
  - license;
  - update/push timestamps;
  - topics;
  - README excerpt.
- Report comparison rows now expose GitHub-specific fields such as `stars`, `forks`, `language`, `license`, `updated_at`, `topics`, and `readme_signal`.

Reference patterns rechecked:

- `browser-use/browser-use`: real browser state plus allowlisted browser tools and page actions.
- `firecrawl/firecrawl`: convert search/crawl/scrape results into clean structured content for downstream agents.
- `TencentCloudADP/youtu-agent`: decompose broad tasks into multi-step tool orchestration.

Verification:

```bash
tests/run_checks.sh
python3 app.py --goal '帮我找几个可以参考的浏览器自动化智能体 GitHub 开源项目，比较活跃度、语言、README质量和适合借鉴的实现点' --domain github --url 'https://github.com' --max-steps 5
```

The latest GitHub run completed with `ok=true`, 10 candidates, and 3 API-backed source readings. The comparison matrix includes stars, language, license, and update timestamps. The artifact is stored in `runs/latest-run-github.json`.

## 2026-05-28 Evidence Scoring For Recommendations

Recommendation output now uses a lightweight evidence scoring layer instead of preserving only candidate discovery order.

Scoring signals by domain:

- GitHub: evidence strength, stars, forks, language, license, topics, README availability, and update metadata.
- Shopping: price signal, review evidence, ANC/noise evidence, comfort evidence, and comparison evidence.
- Video: CLIP/multimodal topic match, tutorial/intro fit, and transcript/segment signals when available.
- General: content evidence from snippets/descriptions.

Report changes:

- `comparison_matrix` rows include `score` and `score_reasons`.
- `recommendations` are generated from the scored matrix and include the same score plus a human-readable evidence reason.

Verification:

```bash
tests/run_checks.sh
python3 app.py --goal '帮我找几个可以参考的浏览器自动化智能体 GitHub 开源项目，比较活跃度、语言、README质量和适合借鉴的实现点' --domain github --url 'https://github.com' --max-steps 5
python3 app.py --goal '预算1000元以内，推荐一款适合通勤和办公室使用的降噪耳机，要比较品牌、类型、价格、音质、降噪、佩戴舒适度和用户评价' --domain shopping --url 'https://www.bing.com' --max-steps 7
python3 app.py --goal '帮我查找并整理一个 CLIP 多模态模型入门教程视频的主要内容' --domain video --url 'https://www.bing.com' --max-steps 6
```

Latest runs all completed with `ok=true`; the top recommendations include scores and evidence reasons in `runs/latest-run-github.json`, `runs/latest-run-shopping.json`, and `runs/latest-run-video.json`.

## 2026-05-28 Markdown Report Export

Runs now produce a human-readable Markdown report in addition to JSON.

Implementation:

- `browser_agent/output/markdown.py` renders the structured run artifact into Markdown.
- CLI writes `runs/latest-report.md` beside `runs/latest-run.json`.
- Backend writes the same Markdown report and exposes it through `GET /api/latest-report`.
- The Markdown report includes summary, visible planning, search plan, ranked recommendations, comparison matrix, source readings, video digest, multimodal notes, uncertainties, next actions, and citations.
- GitHub fallback rows can parse star counts from search snippets when API-backed repo metadata is unavailable, so Markdown still shows useful ranking signals.

Verification:

```bash
tests/run_checks.sh
python3 app.py --goal '帮我找几个可以参考的浏览器自动化智能体 GitHub 开源项目，比较活跃度、语言、README质量和适合借鉴的实现点' --domain github --url 'https://github.com' --max-steps 5
```

The generated `runs/latest-report.md` includes Recommendations, Comparison Matrix, Source Readings, and Citations with evidence scores.

## 2026-05-28 Capability Audit

A requirement-by-requirement acceptance report is available at `docs/capability-acceptance-report.md`.

The original roadmap items have moved as follows:

- Candidate-page deep extraction: implemented for GitHub, shopping, paper/general pages through `deep_read_candidates` and domain-specific readers.
- Optional transcript/video metadata: implemented through visible page text, transcript-like extraction, YouTube oEmbed, optional `yt-dlp` metadata, and structured key-frame fallback.
- Video key-frame sampling: implemented as an optional `yt-dlp` + `ffmpeg` pipeline with safe unavailable status when tools are missing.
- Gemini screenshot/key-frame analysis: implemented as an optional provider path; current environment records unavailable status without `GEMINI_API_KEY`.
- Browser-side task satisfaction scoring: implemented for GitHub, shopping, video, paper, and general tasks in the Chrome extension monitor.
- Browser page actions: implemented through allowlisted search-box filling and verified candidate-link opening.
- Human-readable deliverable: implemented through `runs/latest-report.md` and `GET /api/latest-report`.

Remaining work is enhancement-oriented rather than core objective blocking: configure external media tools/API keys and broaden scoring profiles for more domains.

## 2026-05-28 Similar Plugin UI Review

Similar browser AI assistants reviewed during the frontend pass:

- Monica AI: Chrome extension / all-in-one AI assistant pattern with quick access to chat, writing, search, and multiple models.
- MaxAI.me: browser extension pattern focused on chatting with any webpage, faster reading, and better writing directly where the user works online.
- Merlin-like assistants: in-page/sidebar access to ChatGPT/Claude/Gemini-style helpers for page tasks.
- Perplexity/Comet-style browser assistants: agentic browsing and workflow assistance, with important security lessons around keeping browser actions constrained.

Frontend decisions applied:

- Keep the extension as a compact Copilot control console rather than a raw JSON viewer.
- Add quick task chips for GitHub research, product recommendation, and video summarization.
- Make the running state visible with a top status badge.
- Keep advanced settings collapsed by default.
- Surface Markdown report access directly from the popup.
- Show recommendation scores and score reasons in the report cards.
- Preserve the safe action model: page actions remain allowlisted instead of arbitrary script execution.
