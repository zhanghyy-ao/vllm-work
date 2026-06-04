# API + Browser + Computer Use Test Report

Date: 2026-06-03

## Scope

This round pulled the remote repository updates into the local workspace, resolved merge conflicts, configured DeepSeek locally, and reran regression plus browser/computer checks.

## API Configuration

- Local `.env` exists and is ignored by Git.
- `DEEPSEEK_API_KEY` is configured locally.
- `BROWSER_AGENT_PROVIDER=deepseek`.
- `BROWSER_AGENT_MODEL=deepseek-chat`.
- `BROWSER_AGENT_USE_LLM=true`.

No real API key is stored in tracked source files.

## Regression Tests

Passed:

```bash
tests/run_checks.sh
PYTHONPYCACHEPREFIX=/tmp/vllm-work-pycache python3 -m unittest tests/test_runtime.py
```

Validated areas:

- Python compile checks.
- Chrome extension JavaScript syntax and manifest JSON.
- Chrome monitor rendering tests.
- Popup render tests.
- Python workflow smoke tests.
- New runtime scenario tests from remote main.

## Backend API Test

Backend started successfully:

```bash
python3 backend_api.py
```

Health check:

```json
{"ok": true, "service": "browser-agent-backend"}
```

Executed a DeepSeek-enabled shopping recommendation task:

- Goal: budget under 1000 RMB, recommend commute/office ANC headphones with brand, type, price, sound, ANC, comfort, and user-review comparison.
- Domain: `shopping`.
- Backend result: `ok=true`.
- LLM enabled: `true`.
- LLM plan used: `true`.
- LLM report used: `true`.
- Recommendations: `3`.
- Comparison rows: `3`.

Output artifacts:

- `runs/latest-run.json`
- `runs/latest-report.md`

Top candidates generated:

- Sony WH-CH720N
- Edifier W820NB Plus
- Anker Soundcore Space Q45

## Browser Plugin Test

Browser plugin was tested with the in-app browser.

Result:

- Opened `https://example.com/` successfully.
- Page title detected: `Example Domain`.
- DOM check found `Example Domain`.

Local API pages were not opened through Browser plugin because Browser Use blocked `http://127.0.0.1:8000/...`, `http://localhost:8000/...`, and `file://...` by URL policy. I did not bypass that policy through alternate browser surfaces.

## Computer Use Test

Computer Use successfully read Google Chrome state.

Observed:

- Chrome is running.
- Current page: `chrome://newtab/`.
- Address/search bar is focused.
- Chrome new-tab shortcuts include `Browser Copilot Agent` pointing to `127.0.0.1:8000/`.

## Current Notes

- The codebase is runnable after conflict resolution.
- Browser plugin can operate on allowed web pages.
- Local backend API is reachable by command-line HTTP checks.
- Browser plugin local URL access is blocked by plugin policy, not by the backend.
