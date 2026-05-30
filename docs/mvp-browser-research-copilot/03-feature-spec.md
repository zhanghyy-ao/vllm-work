# 功能说明：Browser Workflow Automation Platform 初版

## 产品定位

这是一个可运行的 Browser Workflow Automation Platform MVP。它不是单纯“自动点网页”，而是把用户目标转成可验证、可恢复、可输出证据链的浏览器工作流。

核心闭环：

```text
Goal -> WorkflowSpec -> Browser Execution -> Verification -> Evidence Memory -> Structured Report
```

## 初版能力

- 自动识别或指定任务域：`github`、`paper`、`shopping`、`video`、`general`
- 显式配置 Agent 和 API provider：默认使用 DeepSeek，支持 agent name、provider、model、API base URL、API key env
- `--use-llm` 开启后，LLM 会参与搜索 query 优化和最终证据报告生成
- 生成确定性 workflow template，便于测试、回放和迭代
- 使用 Playwright 打开真实网页并执行搜索、抽取、链接收集、摘要动作
- 为每一步生成 verification checks 和 event trace
- 将页面链接、标题、正文片段转成 evidence item
- 输出结构化报告：summary、candidates、recommendations、uncertainties、next_actions、citations

## 内置模板

### GitHub 项目发现

输入示例：

```bash
python3 app.py --domain github --goal "帮我找多模态OOD相关开源项目" --url "https://github.com"
```

Workflow：

```text
goto GitHub -> search repositories -> collect candidate links -> summarize recommendations
```

### Paper 调研

输入示例：

```bash
python3 app.py --domain paper --goal "找最近 Agent hallucination 的论文" --url "https://arxiv.org"
```

Workflow：

```text
goto arXiv -> search papers -> collect candidate links -> summarize research leads
```

### Shopping 比较

Workflow：

```text
goto search engine -> search products/reviews -> collect links -> summarize buying recommendation
```

### Video 学习路线

Workflow：

```text
goto video site -> search learning videos -> collect video candidates -> summarize learning path
```

## 输入参数

- `--goal`：必填，用户目标
- `--url`：起始 URL，默认 `https://example.com`
- `--domain`：可选，`auto|github|paper|shopping|video|general`
- `--max-steps`：最多执行节点数，默认 8
- `--headed`：显示浏览器窗口，默认 headless
- `--agent-name`：运行元数据里的 Agent 名称
- `--provider`：API provider，例如 `deepseek`
- `--model`：模型名称
- `--api-key-env`：保存 API key 的环境变量名
- `--api-base-url`：API base URL
- `--use-llm`：启用 LLM planner/summarizer

## Agent/API 配置

默认 provider 是 DeepSeek。没有 API key 时仍可运行规则式 fallback；配置了 `DEEPSEEK_API_KEY` 并传入 `--use-llm` 后，LLM 会真实参与 workflow。

配置优先级：

```text
CLI 参数 > .env > shell environment > 默认值
```

`.env.example` 示例：

```text
BROWSER_AGENT_NAME=browser-workflow-agent
BROWSER_AGENT_PROVIDER=deepseek
BROWSER_AGENT_MODEL=deepseek-chat
BROWSER_AGENT_API_BASE_URL=https://api.deepseek.com
BROWSER_AGENT_API_KEY_ENV=DEEPSEEK_API_KEY
BROWSER_AGENT_USE_LLM=true
DEEPSEEK_API_KEY=
```

## 输出文件

每次运行写入：

```text
runs/latest-run.json
```

关键字段：

- `workflow`：生成的 workflow spec
- `steps`：每个节点的执行结果、验证分数、fallback 信息
- `memory.evidence`：证据链
- `report`：面向用户的结构化报告
- `events`：运行轨迹，便于调试与评测

## 当前边界

- LLM 输出依赖 evidence；证据不足时应输出不确定性，而不是编造结果
- 不处理登录、验证码、付费墙
- 排序质量需要人工复核
- 初版 trace 已保存 event，但还没有实现完整 deterministic replay
