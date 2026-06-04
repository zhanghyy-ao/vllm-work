# 与其他工作的对比

这份文档只保留一个目的：说明当前项目与已有浏览器智能体工作的差异，不做市场宣传，也不堆验收口号。

## 对比对象

- OpenAI Operator / ChatGPT agent
- Anthropic Computer Use
- Browser Use
- Google Project Mariner

这些系统的共同点是：它们强调通用网页操作能力，关注真实浏览器交互、任务完成率和更宽泛的网页覆盖面。

本项目的目标则不同。它不是要在“通用浏览器代理”上全面胜出，而是要把一个课程项目或研究原型最需要的三件事做扎实：

1. 过程可解释
2. 执行可验证
3. 结果可回放

## 本项目的定位差异

### 1. 以 Harness 为中心，而不是以单次 Agent 输出为中心

很多通用浏览器智能体的重点在于“模型如何下一步决定做什么”。本项目虽然也有 LLM 动态规划，但真正的中心不是 planner 本身，而是 `HarnessRuntime`：

- 决定执行路径
- 驱动 observe / act / verify / memory / report 闭环
- 记录事件
- 处理 retry 与 fallback

这意味着本项目更像“带约束的运行时系统”，而不仅仅是“会操作浏览器的模型”。

### 2. 更重视验证和可审计性

当前仓库里，每一步不是执行完就结束，而是要通过 verifier 判断：

- 动作是否成功
- 是否拿到了足够的 evidence 或 fields
- 是否需要 retry

同时，所有关键步骤都会落入：

- `steps`
- `memory`
- `events`
- `metrics`

这种结构特别适合课程展示、实验复盘和工程调试。相比之下，很多通用产品更强调最终任务完成体验，而不一定把中间结构完整暴露出来。

### 3. 研究型任务比通用消费级网页操作更重要

当前项目的强项不在“覆盖尽可能多的网站动作”，而在“围绕证据收集生成结构化结论”。尤其在这些任务里更明显：

- GitHub 项目调研
- 论文检索与比较
- 商品比较与推荐
- 视频内容整理

在这些场景中，系统最终交付的不是“我帮你点了几个网页”，而是：

- evidence
- candidates
- comparison matrix
- recommendations
- uncertainties
- next actions

这和很多通用电脑使用产品的交付目标并不完全一样。

## 和 Browser Use 这类框架的差异

`Browser Use` 更像一个帮助开发者搭建浏览器 agent 的通用框架，重点是 agent 如何感知页面并调用浏览器动作。

本项目则在此基础上，额外强调：

- 固定的数据协议，例如 `Observation`、`WorkflowNode`、`ActionResult`、`StructuredArtifact`
- 运行时的 verifier 和 fallback 机制
- 面向报告输出的 evidence memory
- 场景型和研究型两套执行路径并存

可以把两者的差异理解成：

- Browser Use 更像“浏览器 agent 执行底座”
- 当前项目更像“带评估和交付结构的 Harness 化浏览器研究原型”

## 和 Operator / Computer Use / Mariner 的差异

这些系统更接近通用用户代理，强调：

- 大范围网页导航
- 多站点交互
- 现实世界任务完成
- 更强的端到端自主性

而本项目的侧重点是：

- 较强的结构化输出
- 更明确的安全停顿点
- 更易做课程验收和代码讲解
- 更适合做 runtime、事件流、验证机制的教学示例

因此这不是“谁更强”的单维比较，而是“目标函数不同”：

- 它们优化的是通用能力和真实用户体验
- 本项目优化的是 Harness 清晰度、验证性和工程可解释性

## 当前项目最值得保留的优势

如果只保留几个真正有价值的差异点，我会把它们总结成下面四个：

1. `HarnessRuntime` 是明确的调度中心，不把控制流散落到各处。
2. `Verifier` 是一等模块，失败后有结构化 `retry_hint`。
3. `SessionMemory` 和 `StructuredArtifact` 把证据链和最终交付串起来了。
4. 输出不只是成功/失败，而是完整的 `run -> steps -> events -> report`。

## 不应该夸大的地方

这套系统当前也有边界，文档里需要讲清楚，而不是回避：

- 场景型路径里的 `observe()` 还是 stub，占位性质明显。
- 动态工作流虽然已经存在，但并不是全场景都同样成熟。
- 浏览器动作和视觉理解能力还没有发展成真正的大规模通用 agent。
- 长期 memory、复杂多代理协作和完整 UI 产品化都还在早期。

把这些边界说清楚，反而更能突出当前 Harness 架构本身的价值。
