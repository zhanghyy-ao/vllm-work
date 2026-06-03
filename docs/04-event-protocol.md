# 事件协议（Harness Event）

统一事件对象：

```json
{
  "run_id": "uuid",
  "step_id": 1,
  "phase": "execute_verify",
  "tool": "search",
  "input": {"reason":"先搜集候选"},
  "output": {"result":{"ok":true}, "verdict":{"ok":true}},
  "latency_ms": 123,
  "url": "https://example.com",
  "ts": 1740000000.0
}
```

## 用途

- 调试回放
- 离线评估
- 自进化训练数据
