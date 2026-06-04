# 模块文档：Planner

## 职责
将用户目标转成可执行多步计划（`TaskPlan`），并为每步定义成功标准。

## 输入
- `ResearchRequest`
- 历史偏好（可选）

## 输出
- `TaskPlan`

## 关键接口
- `plan(request: ResearchRequest) -> TaskPlan`
- `replan(context: ReplanContext) -> TaskPlan`

## 失败恢复
- 当 Verifier 连续失败时触发 `replan`
- 自动缩小或改写关键词（如 OOD -> out-of-distribution + multimodal）

## 测试要点
- 相同请求生成稳定步骤数
- 每步包含 `success_criteria`
- 无法解析目标时返回可解释错误
