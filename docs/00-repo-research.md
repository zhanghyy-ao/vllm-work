# GitHub 调研记录

本项目参考了三个开源方向，但不直接照搬大型工程，而是抽取其中适合课程 Demo 的工程边界。

## WebVoyager

- 仓库：`https://github.com/MinorJerry/WebVoyager`
- 价值：提供“观察网页 -> 多模态模型规划 -> Selenium 执行 -> 保存轨迹 -> 自动/人工评测”的端到端 Web Agent 范式。
- 可借鉴点：任务 JSONL、最大交互轮数、截图轨迹、失败分析、text-only 与 multimodal 对比。
- 不直接采用原因：依赖 API Key、Selenium 和论文复现实验，适合作为评测参考，但不适合快速做浏览器插件交互 Demo。

## browser-harness

- 仓库：`https://github.com/browser-use/browser-harness`
- 价值：强调“薄浏览器 Harness + 可编辑任务技能”的工程思想，让 Agent 可以直接连接真实浏览器并逐步沉淀 domain skills。
- 可借鉴点：Harness 层、domain skill、真实浏览器连接、任务执行日志。
- 不直接采用原因：偏 Codex/LLM 控制真实浏览器的开发者工具链，需要用户打开远程调试并配置环境；课程 Demo 更适合先做一个可加载的 Chrome 插件。

## nanobrowser

- 仓库：`https://github.com/nanobrowser/nanobrowser`
- 价值：完整的开源 AI 浏览器自动化插件，包含 side panel、多 Agent、模型配置、任务状态等工程实践。
- 可借鉴点：插件形态、Planner/Navigator 分层、多模型配置、隐私本地化。
- 不直接采用原因：工程较重，依赖 pnpm/Vite/React；作为课程项目起步会把大量时间花在构建系统和 UI 上。

## 本项目取舍

第一版采用轻量工程路线：

- 插件：原生 Manifest V3，无构建步骤。
- Planner：规则 Planner 保底，预留 LLM/VLM Planner 接口。
- Harness：统一 `Observation -> Plan -> Action -> Result` 循环。
- Skills：先实现搜索、表单填写、消息回复三类高频任务。
- 评测：先用本地静态 demo site 验证闭环，再接入 Playwright/browser-harness 做批量测试。

## 进一步功能调研

结合 Operator、Browser-use、BrowseAgent、ChromePilot、AgentSmith、CopilotKiwi 等公开资料，浏览器 Agent 的高频能力可以归纳为：

- 网页任务执行：点击、输入、滚动、导航、多步骤 workflow。
- 表单自动填写：从用户资料、PDF、图片或页面上下文抽取字段并映射到表单。
- 实时搜索与研究：搜索网页、打开结果、总结页面、给出来源。
- 结构化数据抽取：从列表、商品卡片、表格、搜索结果中抽取 CSV/JSON。
- 页面比较：比较价格、功能、评分、日期等字段，生成简短结论。
- 消息/邮件草稿：生成回复内容，但发送前需要用户确认。
- 历史轨迹与回放：保存每一步 action，用于调试和评测。
- 安全控制：对付款、删除、提交、发送等动作设置确认门槛。

因此本 Demo 在搜索、填表、回复之外，新增三个不依赖 API Key 的能力：

- `页面总结`：对当前页面可见内容生成要点式摘要。
- `结构化抽取`：抽取链接、邮箱、价格、列表卡片等信息。
- `结果比较`：对页面中的结果卡片进行简单排序和对比。
