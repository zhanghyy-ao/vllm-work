# GPT-5.5 Switch And Retest - 2026-06-03

## Changes Applied

- Default planner model switched from `gpt-5.4` to `gpt-5.5`.
- Default vision model switched from `gpt-5.4` to `gpt-5.5`.
- Added model fallback lists:
  - `BROWSER_AGENT_MODEL_FALLBACKS=gpt-5.4,gpt-5.4-mini`
  - `BROWSER_AGENT_VISION_MODEL_FALLBACKS=gpt-5.4,gpt-5.4-mini`
- Added stable HTTP user agent header for OpenAI-compatible endpoints.
- Replaced fragile `urllib` LLM calls with `requests`.
- Added retry/fallback behavior for transient `model_not_found` / channel errors.
- Added shorter timeout behavior for final LLM report generation so the agent can degrade more gracefully.

## Verified Results

### Local Validation

- `python3 -m compileall browser_agent` : PASS
- `python3 -m unittest tests.test_runtime` : PASS (15/15)

### Direct Model Probes

- Text planning call through configured OpenAI-compatible endpoint: PASS
- Image-input planning call through configured OpenAI-compatible endpoint: PASS
- The previous `http_403: error code: 1010` blocker is no longer the primary failure mode after switching the request layer and headers.

### Real Browser / Extension Status

- Visible Chrome extension loading had already been proven in the prior real-browser certification run.
- Extension direct browser control had already been proven in the prior real-browser certification run.
- After switching to `gpt-5.5`, backend LLM requests now succeed, so the system is no longer blocked at the old provider-access stage.

## Remaining Issue

A realistic shopping research run with dynamic planning is still taking too long in the backend path.

Observed behavior:
- The bottleneck is no longer the old `403/1010` access denial.
- The backend now spends substantial time inside the deeper browser-agent loop and final report synthesis path for the shopping scenario.
- This means the system has moved from an access/configuration failure into a runtime-convergence/performance issue.

## Practical Interpretation

The project is now in a better state than before:
- Browser control works.
- LLM text calls work.
- LLM multimodal image calls work.
- Model/provider access is no longer the main blocker.

But one more optimization pass is still needed before claiming the shopping scenario is fully market-grade end to end:
- tighten long-running dynamic research steps
- improve convergence for multi-page shopping evidence collection
- keep final report generation bounded and observable

## Recommended Next Optimization Pass

1. Add per-step progress logs into `HarnessRuntime` and `tests/run_real_extension_flow.py`.
2. Add a hard budget for dynamic shopping workflows, such as:
   - max candidate pages opened
   - max deep reads per run
   - max report evidence items
3. Add a lighter report mode for browser-extension live runs.
4. Split certification into:
   - browser control certification
   - backend planning certification
   - end-to-end scenario certification
