# 多场景浏览器智能体工作流设计说明

这份说明把购物之外的 GitHub、论文、视频和通用研究场景也从“一次搜索”升级为可观察、可回退、可验证的多阶段工作流。当前实现进一步把这些阶段从固定动作链降级为 evidence checklist：启用 LLM 时，runtime 每轮根据页面状态动态选择下一步动作。

## 相关工作依据

- [AgentBench](https://github.com/THUDM/AgentBench) 将 LLM Agent 放到多种环境中评测，包括 Web Shopping 和 Web Browsing，说明实用 agent 需要跨环境、多轮交互和环境反馈，而不是单次问答。
- [WebArena](https://arxiv.org/abs/2307.13854)、[Mind2Web](https://arxiv.org/abs/2306.06070) 和 [WebVoyager](https://aclanthology.org/2024.acl-long.371.pdf) 都强调真实网页任务中的状态观察、长程规划和逐步执行。
- [VisualWebArena](https://arxiv.org/abs/2401.13649) 说明大量网页任务依赖视觉信息，文本 DOM 不足以判断页面是否满足任务。
- [PaperQA](https://arxiv.org/abs/2312.07559)、[ResearchPilot](https://arxiv.org/abs/2603.14629) 和相关文献综述 agent 工作强调文献检索需要分阶段执行：找种子论文、扩展相关工作、检查复现资源、总结局限。
- [VideoAgent](https://arxiv.org/abs/2403.10517) 和长视频 agent 工作说明视频理解要通过迭代式问题定位、少量关键帧/视觉工具、字幕/元数据和记忆机制来完成。
- [ReAct](https://arxiv.org/abs/2210.03629) 提供通用执行思想：推理、行动、观察交替，而不是一次性生成不可验证结论。

## GitHub 项目发现

GitHub 场景不再只搜仓库名，而是分阶段：

1. `repo_candidates`：发现候选仓库和同类项目。
2. `repo_metadata`：收集 stars、forks、license、最近更新和 issue 等维护信号。
3. `implementation_docs`：检查 README、安装说明、示例和文档，判断能否落地。
4. `ecosystem_comparison`：寻找竞品、基准和横向比较。

## 论文/相关工作调研

论文场景按文献综述 agent 的流程拆分：

1. `seed_papers`：发现种子论文和核心方法。
2. `related_work`：扩展综述、基准和相关工作脉络。
3. `reproducibility`：检查代码、数据集和复现资源。
4. `limitations`：收集局限性、失败案例和评价指标。

## 视频理解/教程整理

视频场景按 VideoAgent/VisualWebArena 思路拆分：

1. `video_candidates`：搜索主题相关视频候选。
2. `transcript_notes`：寻找字幕、章节、笔记或文字整理。
3. `visual_evidence`：寻找屏幕录制、演示或幻灯片等视觉证据。
4. `comments_discussion`：观察评论区、讨论和常见疑问。
5. 打开视频页后执行 `extract_video`，记录元数据、可见字幕/评论、截图和关键帧预留信息。

## 通用研究

通用研究场景采用三段式证据链：

1. `orientation`：建立背景、关键实体和范围。
2. `primary_sources`：寻找官方文档、原始资料或一手来源。
3. `cross_validation`：寻找替代观点、限制、风险和反例。

## 动态 Agent Loop

启用 `--use-llm` 后，执行过程是：

1. 观察当前页面：URL、标题、正文摘要、候选链接、截图/字段。
2. 读取 memory：已访问页面、证据、最近动作和 verifier 结果。
3. 提供 evidence checklist：例如 `repo_candidates`、`marketplace_pages`、`video_reviews`。
4. LLM 从安全工具集合中选择一个下一步动作：`search_web`、`collect_links`、`open_candidate`、`deep_read_candidates`、`extract_page`、`extract_video`、`summarize_text` 或 `stop`。
5. Browser controller 执行动作。
6. Verifier 判断动作是否成功，结果写入 memory。
7. 如果 checklist 未满足，继续下一轮；满足后总结或停止。

因此，人类定义的是工具、证据要求、安全边界和停止条件；agent 决定下一步搜什么、打开哪个页面、何时深读、何时总结。

## 已补齐的相关工作差距

- 页面观察：每步记录 interactable elements、form fields、visible buttons、selector、bbox、accessibility-style tree、screenshot path 和可选 visual summary。
- 浏览器动作：动态 agent 可选择 `click_element`、`type_text`、`select_option`、`scroll`、`wait`、`back`、`press_key` 等低层动作。
- 动作 grounding：planner 输出 `element_ref`，controller 使用元素 selector 或 `data-agent-idx` 执行点击、输入和选择。
- 多模态进入循环：如果当前 observation 有截图且视觉模型可用，runtime 会先生成页面视觉摘要，再交给下一轮 planner。
- 评估：新增 checklist coverage、final answer groundedness、source citation correctness、browser state goal match 等任务级指标。
- loop recovery：planner 输入包含 visited URLs、search queries、failed actions；重复同一搜索/动作会被拦截。
- 安全：动态动作会拦截 purchase/payment/login/password/delete/submit-order 等敏感意图。

## 实现原则

- `default_search_plan()` 为每个 domain 固化最低可接受的证据阶段。
- DeepSeek/LLM 规划结果会通过 `_augment_search_plan()` 补齐缺失阶段，避免退化成单条泛化搜索。
- `WorkflowNode.inputs.evidence_stage` 会进入报告，前端可以直接展示 agent 当前在做哪类证据收集。
- 确定性 planner 与 LLM planner 使用同一套阶段名，便于测试和后续 UI 监控。
- 研究类 workflow 不再保留旧固定动作模板；当 LLM 不可用时，runtime 返回空动态 workflow shell，不执行浏览器研究动作。
