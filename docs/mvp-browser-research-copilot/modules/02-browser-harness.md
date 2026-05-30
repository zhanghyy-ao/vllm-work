# 模块文档：Browser Harness Runtime

## 职责
统一编排执行循环：调度动作、接收观察、触发验证、执行重试。

## 输入
- `TaskPlan`
- `ActionPolicy`

## 输出
- `StepResult[]`
- `EventLog[]`

## 关键接口
- `run(plan: TaskPlan) -> RunResult`
- `execute_step(step: PlanStep) -> StepResult`
- `retry(step: PlanStep, hint: RetryHint) -> StepResult`

## 状态机
- `INIT -> RUNNING -> VERIFYING -> RETRYING -> DONE|FAILED`

## 失败恢复策略
- 元素找不到：切换定位策略（text -> css -> vision）
- 页面结构变化：回退到搜索页重新定位
- 数据缺失：追加 `extract` 动作补字段

## 测试要点
- Retry 次数上限生效
- 每次失败都产生可追踪事件
- 不会出现死循环状态迁移
