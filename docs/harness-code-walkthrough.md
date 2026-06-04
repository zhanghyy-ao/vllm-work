# Harness 代码讲解

这篇文档按真实代码顺序解释当前 Harness。阅读建议是边看文档边打开代码，不需要先读所有源文件。

## 1. 从 `app.py` 开始

整个程序的入口是根目录下的 `app.py`。

它负责的事情很集中：

1. 解析命令行参数
2. 构造 `AgentConfig`
3. 初始化 `HarnessRuntime`
4. 调用 `runtime.run(...)`
5. 把运行结果写到 `runs/latest-run.json`
6. 把 Markdown 报告写到 `runs/latest-report.md`

也就是说，`app.py` 本身不做业务决策，它只是把一次命令行任务交给 Harness。

### 关键参数

你读 `app.py` 时，最值得注意的是这些参数：

- `--goal`
- `--url`
- `--domain`
- `--max-steps`
- `--headed`
- `--use-llm`
- `--auto-approve-sensitive`
- `--no-market-compare`

这几个参数基本决定了一次运行的行为边界。

## 2. `build_agent_config()` 如何合并配置

接着会进入 `browser_agent/config.py`。

这里定义了 `AgentConfig`，同时提供 `build_agent_config()`。这一步有两个重点。

### 2.1 配置来源不是单一的

当前配置会从下面几处合并：

- CLI 参数
- `.env`
- 环境变量
- dataclass 默认值

所以当你发现运行行为和预期不一致时，不能只看命令行，还要看环境变量有没有覆盖。

### 2.2 配置里不只是模型名

这里除了普通的 provider / model，还包括：

- `model_fallbacks`
- `vision_model_fallbacks`
- `use_llm`
- `use_multimodal_planning`
- `use_visual_precheck`
- `planner_max_tokens`
- `report_max_tokens`

这些字段直接影响 `llm/agent.py` 和 `harness/runtime.py` 的行为。

## 3. `HarnessRuntime.run()` 是真正入口

真正的主逻辑从 `browser_agent/harness/runtime.py` 开始。

`HarnessRuntime.run()` 做的第一件事不是打开浏览器，而是先判断任务该走哪条路径：

- `_run_scenario()`
- `_run_workflow()`

这个分流决定了后面的数据结构、执行器和验证方式都会不同。

## 4. 为什么要分成 `_run_scenario()` 和 `_run_workflow()`

这是当前仓库最重要的设计之一。

### `_run_scenario()`

适合更确定性的任务，例如：

- 预订
- 表单填写
- 监控
- QA

它更像“结构化动作流水线”。

### `_run_workflow()`

适合研究型任务，例如：

- GitHub 调研
- 论文检索
- 商品比较
- 视频整理

它更像“基于 observation 的多轮证据收集循环”。

如果不先理解这个分流，后面看到 `Plan` 和 `WorkflowSpec` 共存时就会很困惑。

## 5. 场景型路径怎么跑

`_run_scenario()` 大致流程如下：

```text
create run_id
  -> create SessionMemory
  -> observe(start_url)
  -> plan_scenario_goal(goal, observation)
  -> for each action in plan.actions:
       execute_action(action, observation)
       verify_step(...)
       memory.write(...)
       make_event(...)
  -> summarize evidence
  -> attach market comparison and metrics
```

### 5.1 初始观察来自 `observe()`

这里调用的是 `browser_agent/browser/observer.py` 里的 `observe()`。

当前实现仍然是 harness-safe stub，它返回一个占位 `Observation`，主要用于：

- 让场景型路径能稳定演示
- 维持统一协议
- 避免在确定性流程里过早依赖完整浏览器观察

这也是当前代码里一个很明显的“还能继续深化”的地方。

### 5.2 动作执行来自 `execute_action()`

`browser_agent/browser/action.py` 里的 `execute_action()` 会根据 `Action.tool` 做受控分发。

目前这个接口的特点是：

- 每种工具有固定 outcome 文案
- 输出统一结构化字典
- 不直接暴露底层复杂状态

这让场景型路径在调试和讲解时都比较稳定。

### 5.3 敏感动作会暂停

如果一个动作被标记为 `sensitive`，而用户没有传 `--auto-approve-sensitive`，那么 runtime 不会继续执行，而是返回：

- `awaiting_user_approval`
- `approval_requests`

这是当前系统安全设计里非常明确的一环。

## 6. 研究型路径怎么跑

更核心的是 `_run_workflow()`。

这条链路大致如下：

```text
create run_id
  -> create SessionMemory
  -> create initial Observation
  -> plan_goal(goal, observation, domain)
  -> open BrowserSession
  -> repeat by step:
       ask dynamic planner for next node
       execute node
       verify result
       write memory
       refresh observation
       append step output
  -> build_report(...)
  -> optionally enhance with LLM report
  -> return result payload
```

这就是当前项目最核心的 Harness 闭环。

## 7. `plan_goal()` 到底产出什么

`browser_agent/planner/tot.py` 并不总是一次性给出完整固定动作链。

对研究型任务来说，当前 planner 更像是在做两件事：

1. 判断 domain
2. 生成工作流骨架 `WorkflowSpec`

这意味着：

- workflow 一开始可能没有很多固定 node
- 真正执行过的 node 会在运行时追加到 `workflow.nodes`

这和传统“先完整规划，再逐步执行”的固定脚本模式不同。

## 8. 动态下一步决策在哪里发生

当 `llm_client.enabled` 为真时，runtime 会调用：

- `browser_agent/llm/agent.py` 中的 `plan_next_action()`

这个函数会综合：

- 当前 `Observation`
- `memory_dump`
- 最近 `step_outputs`
- `default_search_plan()` 提供的 checklist

然后从一组受限动作中选出下一步，例如：

- `search_web`
- `collect_links`
- `open_candidate`
- `deep_read_candidates`
- `extract_page`
- `extract_video`
- `summarize_text`
- `stop`

同时它还会限制敏感意图，例如：

- login
- payment
- delete
- purchase

因此动态规划并不是“让模型随意发挥”，而是“在 Harness 允许的动作空间里做下一步选择”。

## 9. 为什么 `tool_dispatch.py` 这么薄

`browser_agent/harness/tool_dispatch.py` 基本只做一件事：

- 把 `WorkflowNode` 转交给 `BrowserSession.execute()`

这看起来很薄，但设计上是合理的。原因是：

- 调度逻辑放在 runtime
- 浏览器动作细节放在 browser 层
- tool dispatch 保持极轻，避免中间层再长出业务

这样分层后，后续要换执行器或加代理层，也更容易演进。

## 10. `BrowserSession` 为什么这么关键

`browser_agent/browser/action.py` 里的 `BrowserSession` 是研究型路径真正接触网页的地方。

它内部基于 Playwright，负责：

- 启动和关闭浏览器
- 打开页面
- 执行搜索
- 收集候选链接
- 打开候选页
- 抽取正文与字段
- 记录截图与页面快照
- 把当前页面重新组织成新的 `Observation`

也就是说，`BrowserSession` 不只是“浏览器控制器”，也是“Observation 生产器”。

这点非常重要，因为下一轮 planner 看到的页面状态，就是它整理出来的。

## 11. `_execute_with_retries()` 是运行稳定性的核心

在 `_run_workflow()` 里，最值得读的辅助函数之一是 `_execute_with_retries()`。

它会：

1. 执行当前 node
2. 调用 `verify_node()`
3. 如果失败，根据 `retry_hint` 构造 fallback node
4. 在重试上限内继续尝试
5. 最终生成 event

这个函数的价值在于，它把“失败处理”从散落的 if/else 提升成统一策略。

例如：

- `search_web` 首次失败时，可以回退到通用搜索
- `collect_links` 失败时，可以改成 `extract_page`

这就是 Harness 与普通脚本自动化的差别之一。

## 12. Verifier 在代码里具体怎么工作

`browser_agent/verifier/critic.py` 里有两套接口：

- `verify_step()`
- `verify_node()`

### `verify_step()`

用于场景型路径，逻辑更简单，主要判断：

- 工具是否在允许集合里
- 输出 `ok` 是否为真

### `verify_node()`

用于研究型路径，检查更完整：

- `action_ok`
- `page_reachable`
- `evidence_or_fields`
- 对某些抽取动作再检查内容是否为空

然后给出 `VerificationResult`，里面最关键的是：

- `score`
- `retry_hint`

这是 runtime 后续决策的重要依据。

## 13. `SessionMemory` 为什么看起来简单却很重要

`browser_agent/memory/session.py` 的实现很短，但在主链路里的位置非常关键。

它主要做两件事：

1. 保存 `traces`
2. 累积 `evidence`

你可以把它理解成一次运行的“中间事实仓库”。

后面的两个模块都依赖它：

- planner 读取 memory 以避免重复动作
- report builder 读取 evidence 组织最终报告

因此 Memory 不是附属日志，而是闭环里的中枢缓冲层。

## 14. `HarnessEvent` 为什么值得单独看

`browser_agent/harness/events.py` 定义了 `HarnessEvent` 和 `make_event()`。

每个事件都会记录：

- `run_id`
- `step_id`
- `phase`
- `tool`
- `input`
- `output`
- `latency_ms`
- `url`
- `ts`

这意味着如果你要做：

- 调试回放
- 运行分析
- 指标统计
- 训练数据沉淀

事件流会是最直接的抓手。

## 15. 报告生成阶段怎么收尾

执行循环结束后，runtime 会调用：

- `build_report()`
- `build_llm_report()`

### `build_report()`

`browser_agent/output/report_builder.py` 会把：

- `workflow`
- `memory_dump`
- `steps`

整理成 `StructuredArtifact`。

输出内容通常包括：

- summary
- candidates
- source_readings
- recommendations
- reasoning_outline
- comparison_matrix
- uncertainties
- next_actions
- citations

### `build_llm_report()`

如果模型可用，再用 LLM 对报告做增强，让最终结论更像面向人的研究总结，而不是原始字段拼接。

## 16. 最终返回给外部的结果长什么样

`HarnessRuntime.run()` 最终会构造一个大的 `result_payload`。通常包含：

- `run_id`
- `agent`
- `llm`
- `goal`
- `start_url`
- `workflow` 或 `plan`
- `steps`
- `memory`
- `report`
- `events`
- `ok`
- `metrics`

这个结构本身就体现了当前项目的设计哲学：不是只给一个答案，而是给一份完整运行记录。

## 17. 最值得优先阅读的代码文件

如果要真正吃透当前 Harness，我建议按下面顺序看代码：

1. `app.py`
2. `browser_agent/harness/runtime.py`
3. `browser_agent/types.py`
4. `browser_agent/planner/tot.py`
5. `browser_agent/browser/action.py`
6. `browser_agent/verifier/critic.py`
7. `browser_agent/memory/session.py`
8. `browser_agent/harness/events.py`
9. `browser_agent/output/report_builder.py`
10. `browser_agent/llm/agent.py`

这个顺序的好处是先掌握主控制流，再补细节。

## 18. 当前代码最清楚的优点和最明显的边界

### 优点

- 主控制中心明确，`HarnessRuntime` 很清晰。
- 协议层统一，模块之间传递结构化对象。
- verifier、memory、event、report 已经接上了闭环。
- 动态 agent 和确定性场景两条链路可以并存。

### 边界

- 场景路径里的 `observe()` 还是 stub。
- 一些能力仍然更偏课程原型，而不是完整产品。
- 多模态与长期记忆还处在扩展位阶段。

## 19. 一句话理解这份代码

当前这套代码的重点不是“会不会点网页”，而是把浏览器任务组织成一条可规划、可验证、可追踪、可交付的 Harness 运行链。
