# `agent_py` 代码全量梳理（逐文件 + 逐函数）

本文目标：把 `agent_py/` 下每个文件、每个类/函数的功能与实现方式讲清楚，便于开发、答辩和二次重构。

## 1. `agent_py/__init__.py`

功能：包入口导出。

- 导出对象：`BrowserAgentRunner`, `BrowserHarness`, `LLMConfig`, `observe_html`, `plan_task`, `plan_with_llm`
- 实现方式：纯 re-export，无业务逻辑。

## 2. `agent_py/config.py`

功能：环境变量加载。

- `load_dotenv(path=None)`
  - 功能：从 `.env` 读取键值到 `os.environ`。
  - 实现：逐行解析 `KEY=VALUE`，忽略空行/注释；不覆盖已存在环境变量（保证外部注入优先）。

## 3. `agent_py/schema.py`

功能：全系统数据结构定义。

- `Element`
  - 功能：统一描述交互元素（id/selector/role/label/href/form上下文等）。
  - `haystack()`：拼接所有可检索字段，供匹配打分。
- `Observation`
  - 功能：页面观测快照（文本、元素、cards、tables、links、prices、headings、截图路径等）。
- `Action`
  - 功能：计划动作模型（type/target/value/key/reason/risk）。
  - `to_dict()` / `from_dict()`：与前端 JSON 协议互转。
- `Plan`
  - 功能：计划容器（summary/confidence/warnings/actions）。
  - `to_dict()` / `from_dict()`：序列化与反序列化。
- `ActionResult`
  - 功能：单步动作执行结果（ok/output/error/url/artifact）。
- `ExecutionResult`
  - 功能：整次执行结果（logs + artifact + trajectory）。
  - `ok`：所有日志都成功才为 True。

## 4. `agent_py/html_model.py`

功能：轻量 HTML 解析树（离线观测使用）。

- `Node`（类）
  - `text()`：递归提取文本（忽略 script/style/noscript）。
  - `attr()`：安全获取属性。
  - `find_all()`：递归查找节点。
  - `first()`：找首个匹配节点。
- `TreeParser(HTMLParser)`（类）
  - `handle_starttag/endtag/data`：构造 Node 树。
- `parse_html(html)`：返回根节点。
- `normalize_space(text)`：空白规范化。

实现：不依赖浏览器内核，适合测试和静态页面解析。

## 5. `agent_py/observer.py`

功能：把 HTML 转为标准 `Observation`。

- `observe_html(html, url="about:blank")`
  - 功能：核心入口，抽取 title/text/elements/cards/tables/links/emails/prices/headings。
  - 实现：基于 `html_model` 的 DOM 树规则提取。
- `observe_file(path, url=None)`：文件版入口。
- 元素定位与标签函数：
  - `_css_escape`, `_selector_for`, `_selector_path`, `_selector_step`, `_nth_of_type`
  - 用途：构造可复用 selector。
- 语义上下文函数：
  - `_ancestor_attr`, `_section_label`, `_labels_by_for`, `_label_for`, `_implicit_role`, `_is_interactive`
  - 用途：把输入框和标签/区域关联，减少误匹配。
- 结构化抽取函数：
  - `_collect_links`, `_collect_cards`, `_collect_tables`, `_unique_by`
  - 用途：为 compare/research 提供候选数据。

## 6. `agent_py/planner.py`

功能：规则规划器（LLM 不可用或兜底路径）。

- `plan_task(command, observation)`
  - 功能：任务意图识别并分派到具体子计划。
  - 实现：正则路由（search/form/reply/research/docs/find/summarize/collect/compare 等）。
- 意图判断函数：
  - `_is_search_task/_is_form_task/_is_reply_task/_is_research_task/_is_github_brief_task/_is_ui_analysis_task/_is_project_analysis_task/_is_find_task/_is_docs_task/_is_summarize_task/_is_collect_task/_is_compare_task`
- 计划生成函数：
  - `_plan_search`, `_plan_web_search`, `_plan_form_fill`, `_plan_reply`, `_plan_brief`, `_plan_docs_brief`, `_plan_find`, `_plan_compare`, `_plan_click_or_extract`
  - 实现方式：构造 `Plan(actions=[...])`，动作类型符合 schema。
- 文本清洗函数：
  - `_clean_search_query/_clean_reply_text/_clean_compare_focus/_clean_find_query/_parse_fields/_detect_collect_target`
- 元素匹配/打分函数：
  - `_best_element/_best_form_context/_best_field_element/_score_field_element/_context_elements/_element_context/_best_click_target/_matching_cards/_focus_tokens/_score_element/_is_text_input/_is_clickable/_is_search_submit/_name`
  - 实现重点：优先 label/name/placeholder + form/section 上下文，降低跨区域误填。

## 7. `agent_py/safety.py`

功能：计划安全净化与风险拦截。

- `sanitize_plan(plan, observation, allow_explicit_submit=False)`
  - 功能：过滤非法 action type/targetId，并对每步调用 `guard_action`。
- `guard_action(action, observation, allow_explicit_submit=False)`
  - 功能：识别高风险点击/回车动作，必要时转换为 `highlight`。
- `_is_allowed_explicit_submit`：仅在用户显式允许时放开普通提交/发送。
- `_is_search_submission`：搜索提交白名单（避免误拦截搜索按钮）。
- `_target_haystack`：拼接目标元素文本用于风险判断。
- `is_high_risk_action`：外部风险判定接口。
- `valid_action_types`：返回动作白名单。

实现策略：付款/删除/上传/下单/权限类硬风险持续拦截。

## 8. `agent_py/llm_planner.py`

功能：LLM 规划与文本补全统一通道。

- `LLMConfig`
  - 字段：`api_base/api_key/model/temperature/timeout`
  - `from_env()`：从 `.env` 读取（默认 synai 通道配置）
  - `enabled`：是否可用
  - `transport`：推断 `openai-chat` 或 `gemini-native`
- `plan_with_llm(task, observation, config, allow_explicit_submit=False)`
  - 功能：发起 LLM 规划，解析为 `Plan`，再走 `sanitize_plan`。
- `infer_transport/_use_gemini_native_api/_is_gemini_model`
  - 功能：通道判定。
- `request_text_completion(messages, config, temperature=None)`
  - 功能：统一文本请求入口。
- `_call_gemini_messages`
  - 功能：Gemini `generateContent` 调用路径。
- `_primary_gemini_url/_messages_to_gemini_prompt`
  - 功能：构造请求 URL 与 prompt。
- `_looks_like_html_response`
  - 功能：防止网关返回网页而非 JSON。
- `_explain_synai_error`
  - 功能：把异常翻译成可读告警。
- `build_system_prompt`
  - 功能：约束 LLM 输出 JSON + 动作规范 + 安全规则。
- `compact_observation`
  - 功能：压缩 observation，控制 token。
- `parse_plan`
  - 功能：从原始文本提取 JSON 并转 `Plan`。
- `_post_json`
  - 功能：HTTP POST + retry + 错误规范化。
- `try_plan_with_llm`
  - 功能：失败返回 `None` 的轻量入口。

## 9. `agent_py/comparison.py`

功能：候选构建、比较、推荐（规则与 LLM 双路径）。

- `generate_comparison(command, observation, memory=None, llm_config=None)`
  - 功能：返回可读文本比较结果。
  - 实现：先建候选，再优先 LLM，否则规则排序。
- `recommend_from_observation(..., require_llm=True)`
  - 功能：返回结构化推荐 JSON（comparisonTable/topPick/why/evidence/confidence）。
  - 实现：可强制 LLM；若开启强制且失败，返回 `llm_required_failed`。
- `build_candidate_set(observation, memory=None)`
  - 功能：合并 cards/tables/memory 快照并去重、去噪、补细节上下文。
- `select_sampling_candidates(...)`
  - 功能：选出 2~3 个详情页采样目标。
- `_compare_with_rules/_compare_with_llm`
  - 功能：文本比较两条路径。
- `_recommend_with_llm_json`
  - 功能：要求 LLM 严格输出推荐 JSON。
- `_simple_comparison_table`
  - 功能：规则降级时生成简表。
- `_parse_compare_json/_render_llm_result`
  - 功能：解析与渲染 LLM 输出。
- `_table_candidates/_normalize_candidate/_apply_detail_context`
  - 功能：结构标准化、融合 memory 详情页证据。
- `_score_candidate`
  - 功能：多维打分（相关性、评分、价格、特征、详情强度）。
- 其余辅助函数：
  - `_clean_compare_focus/_focus_tokens/_extract_features/_filter_aggregate_candidates/_render_table/_table_cell/_looks_like_aggregate_title/_winner_reason/_find_date/_to_price/_to_rating/_first_index`

## 10. `agent_py/memory.py`

功能：运行记忆与分支合并（支持多轮、多分支推荐）。

- `AgentMemory`（类）
  - 字段：搜索词、已访问 URL、候选快照、详情页、worker/branch/merge 等。
- `remember(action, observation, output=None, artifact="")`
  - 功能：每步执行后写记忆（搜索词、候选快照、产物统计）。
- `to_dict()`
  - 功能：导出给 API/LLM。
- `summary()`
  - 功能：生成简短记忆摘要。
- `remember_workflow(task_queue, workers, branches)`
  - 功能：记录阶段队列和并行状态。
- `merge_branch_result(branch_result)`
  - 功能：把并行分支结果并入全局候选池和证据图。
- `remember_detail_page(candidate, observation, summary="", metadata=None)`
  - 功能：保存详情页采样证据。
- `_target/_page_summary`（静态方法）
  - 功能：目标元素查找与页面摘要拼装。
- 全局辅助函数：
  - `_is_boilerplate_line/_extract_title_tagline/_clean_string_list/_pick_semantic_lines`

## 11. `agent_py/executor.py`

功能：离线/测试执行器（非真实浏览器）。

- `BrowserHarness`（类）
  - 功能：在内存 observation 上执行动作，便于测试规划器和逻辑。
  - `run(plan)`：顺序执行并返回 `ExecutionResult`。
  - `execute(action)`：分 action type 执行。
  - 其余方法（类内）负责：
    - `_target` 目标定位
    - `_maybe_submit_search` 搜索行为模拟
    - `extract/summarize/collect/compare/brief/find/copy` 产物生成
- `_score_text(text, query)`
  - 功能：文本匹配简单打分。

实现特点：不依赖 Playwright，跑单测快、可控性高。

## 12. `agent_py/browser_runtime.py`

功能：真实浏览器运行时（Playwright + CDP）。

- `PlaywrightBrowserRuntime`（类）
  - `start()`：优先连接 CDP Chrome，失败回退临时 Chromium。
  - `close()`：释放资源；CDP 模式仅断开连接。
  - `goto(url)`：导航并返回 observation。
  - `observe()`：抓取当前 live observation。
  - `_build_observation(page, capture_screenshot)`：HTML + live 元素融合。
  - `screenshot(path)`：显式截图。
  - `run(plan)`：执行完整计划，记录 trajectory。
  - `execute(action)`：执行单动作。
  - 定位相关：
    - `_locator_for/_element_for/_locator_from_element/_best_locator_candidate`
    - 作用：selector 优先，失败后按语义重定位。
  - 行为相关：
    - `_highlight_locator/_click_locator/_wait_after_action`
    - `_extract/_collect/_compare/_static_result/_sample_detail_pages`
  - 观测相关：
    - `_live_elements/_best_live_match/_observation_summary/_capture_observation_screenshot`
  - 健壮性：
    - `_ensure_page/_select_active_page` 等保护函数。

核心实现：每步动作后重观测，保证动态页面可持续执行。

## 13. `agent_py/workflow.py`

功能：阶段队列与并行分支控制器模型。

- 数据类：
  - `WorkflowTask`：任务节点（phase/title/goal/status/depends_on/merge_key 等）
  - `WorkerState`：worker 运行状态
  - `BranchResult`：分支产出
  - `MemoryMergeRecord`：合并日志
  - `ControllerResult`：前端展示总对象
- `build_workflow_controller(task, observation, plan, planner_source, ...)`
  - 功能：构建“主队列 + 分支 + worker + 当前阶段”结构。
- `is_parallel_workflow_task(task)`
  - 功能：判定是否适合并行（比较/研究类）。
- `_base_queue`
  - 功能：固定阶段骨架（observe -> understand -> decompose -> plan -> execute -> finalize）。
- `_parallel_branches/_compare_branches/_research_branches`
  - 功能：按任务类型派生并行分支。
- `_phase_reasoning`
  - 功能：为 UI 生成当前阶段解释文本。
- `_is_compare_task/_is_research_task/_clean_compare_focus`
  - 功能：并行任务判定与焦点清洗。

## 14. `agent_py/runner.py`

功能：总调度器（把观察、规划、执行、记忆、工作流串起来）。

- `AgentRunResult`（数据类）
  - 功能：一次任务的最终返回对象。
  - `to_dict()`：输出给 CLI/Web UI。
- `BrowserAgentRunner`（类）
  - `__init__(...)`：注入 llm/headless/cdp/max_steps/screenshot/safety 选项。
  - `run(url, task)`
    - 功能：主入口。
    - 实现流程：
      1. 初始化 `AgentMemory` + `PlaywrightBrowserRuntime`
      2. 首次观察
      3. 规划（LLM 优先，失败则规则）
      4. 安全净化 + 计划补全
      5. 执行动作并循环重规划（最多 `max_steps`）
      6. 生成 workflow/memory/trajectory 并返回
  - 类内辅助（已在文件中定义）：
    - `_complete_plan`：补齐结果动作（extract/summarize/copy 等）
    - `_plan_with_source`：返回 plan + planner source + warning
    - `_execute_parallel_branches_if_needed`：并行分支执行与合并（研究/比较任务）
    - 以及与 workflow/memory 交互的拼装函数。
- 文件级辅助函数：
  - `_looks_like_search_task/_needs_artifact/_has_result_action/_query_from_plan/_observation_summary`
  - `save_trajectory(result, path)`：落盘完整结果 JSON。

## 15. `agent_py/web_app.py`

功能：Flask 服务（插件 API + 本地 UI）。

- `create_app()`
  - 功能：创建 app、挂载路由、设置 CORS。
  - 路由：
    - `/api/extension/health`：后端健康状态
    - `/api/extension/plan`：计划生成（推荐任务可强制 LLM）
    - `/api/extension/recommend`：保存推荐上下文 JSON + 生成结构化推荐结果
    - `/`：Web UI 表单页
    - `/download/trajectory.json`：下载轨迹
    - `/artifact/screenshot`：读取截图
- `run_app(host, port, debug)`：启动入口。
- `_pretty`：JSON 格式化给 UI。
- `_check_cdp`：探测 CDP 可用性。
- `_screenshots`：提取轨迹截图列表。
- `_observation_from_extension`：扩展 observation 映射到 `Observation`。
- `_task_mode/_is_recommendation_task`：任务分类。
- `_llm_failure_code`：LLM 错误码归一化。
- `_persist_recommendation_payload`：推荐请求落盘到 `runs/recommendation/recommend-*.json`。

---

## 16. 关键实现机制总结

1. 双规划器机制：LLM 优先，规则兜底；推荐任务可切到 LLM 强制失败即中断。  
2. 安全层前置：所有计划先过 `sanitize_plan`，避免危险动作直接执行。  
3. 观察-执行闭环：真实浏览器每步动作后重新观察，减少 DOM 失效。  
4. 记忆驱动推荐：候选快照 + 详情页采样 + 分支合并，支撑综合推荐。  
5. 产物化输出：比较/研究结果统一生成 artifact，并支持 JSON 持久化。

