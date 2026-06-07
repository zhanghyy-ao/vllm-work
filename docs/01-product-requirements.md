# Browser Copilot Agent 产品需求

## 目标

构建可真实落地的浏览器自动协助智能体，采用 Harness Runtime 思路，而非单次脚本自动化。

## 核心定义

`Browser Agent = vLLM + Browser Harness + Memory + Verification + Self-evolution`

## MVP 功能

1. 研究检索场景：搜索 -> 摘要 -> 来源
2. 表单草稿场景：识别字段 -> 填写 -> 验证
3. 比较推荐场景：候选采样 -> 对比 -> 推荐

## 验收

- 主流程可稳定执行：observe -> plan -> execute -> verify -> memory
- 每个任务输出 artifact
- 关键事件可追踪和回放
