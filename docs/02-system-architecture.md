# 系统架构

```text
User Goal
  ->
Planner Agent
  ->
Harness Runtime
  ->
Tool Dispatcher / Browser Executor
  ->
Verification Agent
  ->
Memory (Session + Long-term)
```

## 架构原则

1. Harness 优先：模型可替换，运行时稳定
2. 验证优先：每步执行后检查成功性
3. 记忆优先：跨步骤/跨页面复用上下文
4. 可观测优先：所有动作事件化
