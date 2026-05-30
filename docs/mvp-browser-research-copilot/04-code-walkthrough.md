# 代码阐释：Browser Workflow Automation Platform 初版

## 入口

`app.py` 是 CLI 入口。它解析 `goal/url/domain/max-steps/headed`，创建 `HarnessRuntime`，运行后把完整结果写入 `runs/latest-run.json`。

同时它会构造 `AgentConfig`，支持从 CLI、`.env` 或环境变量读取 provider、model、API base URL 和 API key 环境变量名。默认 provider 是 DeepSeek。

## Agent/API 配置

`browser_agent/config.py` 定义 `AgentConfig`。

当前字段：

- `agent_name`
- `provider`
- `model`
- `api_key_env`
- `api_base_url`
- `use_llm`
- `api_key_configured`

`browser_agent/llm/client.py` 提供 OpenAI-compatible chat client。配置 `DEEPSEEK_API_KEY` 并传入 `--use-llm` 后，runtime 会真实调用 DeepSeek。

LLM 当前参与两个位置：

- `enhance_workflow_with_llm()`：把用户目标改写成更适合搜索的 query
- `build_llm_report()`：基于 evidence 生成中文 summary、recommendations、uncertainties、next_actions

## 核心类型

`browser_agent/types.py` 定义平台协议：

- `WorkflowSpec`：一次任务的完整工作流
- `WorkflowNode`：可执行节点，包含 action、inputs、success criteria、retry policy
- `ActionResult`：浏览器执行结果
- `VerificationResult`：Verifier 的检查结果
- `EvidenceItem`：可追溯证据
- `StructuredArtifact`：最终报告

旧版 `Action/Plan` 被保留，用于兼容原始骨架和简单调用。

## Planner

`browser_agent/planner/tot.py` 的 `plan_goal()` 负责把自然语言目标转成 `WorkflowSpec`。

它会根据 `--domain` 或关键词识别任务域：

- `github`：开源项目发现
- `paper`：论文检索
- `shopping`：商品比较
- `video`：视频学习路线
- `general`：通用研究

初版使用确定性模板，优点是稳定、容易测试，也方便后续引入 LLM planner 做替换。

## Browser

`browser_agent/browser/action.py` 封装 `BrowserSession`，负责真实 Playwright 操作。

支持动作：

- `goto`：打开页面
- `search_web`：根据 source 生成搜索 URL
- `extract_page`：抽取正文和截图
- `collect_links`：收集候选链接
- `summarize_text`：生成轻量摘要证据

所有异常都会转成 `ActionResult`，避免浏览器错误直接打断整个程序。

## Harness

`browser_agent/harness/runtime.py` 是主循环：

```text
create workflow -> open browser -> execute node -> verify -> write memory -> update observation -> build report
```

失败时会进入 `_fallback_node()`：

- `search_web` 首次失败时切换到通用搜索
- `collect_links` 失败时退回 `extract_page`
- 每个节点默认最多重试 2 次

每个节点都会通过 `make_event()` 写入 trace。

## Verifier

`browser_agent/verifier/critic.py` 的 `verify_node()` 做基础质量检查：

- action 是否成功
- 页面 URL 是否存在
- 是否有 evidence 或 fields
- 对抽取/摘要节点，内容是否非空

输出 `score` 和 `retry_hint`，由 Harness 决定是否 fallback。

## Memory

`browser_agent/memory/session.py` 保存当前 run 的 trace 和 evidence。

Memory 现在是会话级的，后续可以扩展为：

- workflow template memory
- user preference memory
- evidence vector index

## Report

`browser_agent/output/report_builder.py` 把 evidence 汇总成用户可读报告：

- `summary`
- `candidates`
- `recommendations`
- `uncertainties`
- `next_actions`
- `citations`

报告生成只依赖 memory，不直接访问浏览器，方便测试和后续换输出格式。

## 验证命令

```bash
python3 -m compileall browser_agent app.py
DEEPSEEK_API_KEY=... python3 app.py --domain github --goal "帮我找多模态OOD相关开源项目" --url "https://github.com" --use-llm
DEEPSEEK_API_KEY=... python3 app.py --domain paper --goal "找最近 Agent hallucination 的论文" --url "https://arxiv.org" --use-llm
```
