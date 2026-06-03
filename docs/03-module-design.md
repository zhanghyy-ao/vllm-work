# 模块设计

## planner/

- `tot.py`: 任务拆解（ToT 风格）

## browser/

- `observer.py`: 页面观测
- `action.py`: 浏览器动作执行

## harness/

- `runtime.py`: 主循环
- `tool_dispatch.py`: 工具分发
- `events.py`: 事件结构

## verifier/

- `critic.py`: 单步验证

## memory/

- `session.py`: 会话记忆
- `rag.py`: 长期记忆检索占位

## vision/

- `grounding.py`: 视觉定位占位

## evaluation/

- `metrics.py`: 基础评测指标
