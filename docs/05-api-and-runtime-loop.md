# Runtime Loop 说明

主循环由 `browser_agent/harness/runtime.py` 实现：

1. `observe(start_url)`
2. `plan_goal(goal, observation)`
3. 对每个 action：
   - `dispatch(action, observation)`
   - `verify_step(tool, output, observation)`
   - `memory.write(...)`
   - `emit event`

输出结构：

- `plan`
- `steps`
- `memory`
- `events`
- `ok`

运行命令：

```bash
python3 app.py --goal "帮我比较三款耳机并推荐"
```
