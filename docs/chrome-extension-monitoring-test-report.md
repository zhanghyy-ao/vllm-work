# Chrome Extension Browser-Control Test Report

Date: 2026-05-28

## Scope

Tested the Chrome extension frontend integrated with the existing backend API. The focus was real Chrome tab control plus continuous browser-state monitoring: observe the current page, judge whether it satisfies the task, and continue navigating when it does not.

## Environment

- Workspace: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work`
- Backend: `backend_api.py`
- Backend health endpoint: `http://127.0.0.1:8000/api/health`
- LLM provider: DeepSeek via `DEEPSEEK_API_KEY`
- Chrome extension ID: `oplcpkcgdnoanloopllmieljekadacnf`
- Loaded extension path: `/Users/zhanghyy-ao/.codex/worktrees/833c/vllm-work/chrome_extension`
- Project extension path: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/chrome_extension`

## Implemented Capabilities

- Popup sends the task to a background service worker instead of doing long-running work inside the popup.
- Background service worker controls the active Chrome tab via `chrome.tabs.update`.
- Background service worker calls the local backend `/api/run` with DeepSeek-enabled planning.
- After backend completion, the extension opens the backend-produced final URL in the active tab.
- Monitoring loop observes the real page with `chrome.scripting.executeScript`.
- Monitoring loop scores whether the page satisfies the task.
- If the page is not satisfactory, the extension derives follow-up URLs from the live page and continues navigation.
- GitHub search handling avoids accepting zero-result pages as success.
- GitHub repository detection now rejects marketing/navigation pages such as `/security/*` and `/solutions/*`.
- For GitHub tasks, success requires a real repository-shaped page with repository UI signals such as Code, Issues, README, stars, forks, or commits.

## Test Cases

### Case 1: Unsatisfied Search Should Continue Or Request Review

Task: `搜索 CLIP OOD GitHub 开源项目`

Observed behavior:

- The plugin controlled the current Chrome tab from `github.com`.
- Backend generated a GitHub repository search URL.
- The GitHub repository search had no matching repositories.
- The monitor refused to treat the zero-result repository search as satisfied.
- Earlier versions over-followed GitHub marketing links; this was fixed by tightening GitHub repository URL filtering and keyword matching.
- Final status became `needs_review` when no confident repository target was available.

Result: Pass. The extension did not falsely mark the original zero-result page as successful after the filtering fix.

### Case 2: Satisfied Search Should Reach A Real Repository Page

Task: `搜索 openai CLIP GitHub 开源项目`

Observed behavior:

- The plugin controlled the current Chrome tab from `github.com`.
- Backend generated `https://github.com/search?q=openai+CLIP+GitHub&type=repositories`.
- The monitor inspected the search page and derived a repository candidate from the live page links.
- The active Chrome tab was navigated to `https://github.com/stanislavfort/OpenAI_CLIP_adversarial_examples`.
- The final page is a real GitHub repository page and includes Code, Issues, README, stars/forks, and About signals.

Result: Pass. The extension demonstrated real browser control and monitor-driven continuation to a task-satisfying page.

## Validation Commands

```bash
curl -sS http://127.0.0.1:8000/api/health
node --check chrome_extension/background.js
node --check chrome_extension/popup.js
python3 -m json.tool chrome_extension/manifest.json >/dev/null
```

All validation checks passed.

## Notes

- The backend was started with the DeepSeek key in the process environment, not written into source files.
- The extension must be reloaded from `chrome://extensions` after source changes.
- The loaded Chrome extension path and project extension path were kept in sync.
- The popup now stores monitoring observations in `chrome.storage.local`, so the status can be reopened after the popup closes.
