# 后端代码梳理（Python Browser Agent）

## 1. 后端范围

本项目“后端”核心为 Python 代码，主要分布在：

- `agent_py/`：核心业务逻辑（观测、规划、执行、安全、比较、记忆、工作流、Web API）
- `scripts/`：后端启动与验收脚本
- `tests/`：后端相关单元/接口/流程测试

---

## 2. 总体架构与调用链

### 2.1 插件链路

1. Chrome 插件采集页面 observation（`extension/content.js`）
2. 调用 Python API：`POST /api/extension/plan`
3. Python 后端返回计划（规则或 LLM）
4. 插件执行动作后回传执行结果
5. 推荐任务调用 `POST /api/extension/recommend`
6. 后端把 observation+execution 落盘为 JSON，并调用 LLM 输出推荐结果

### 2.2 Python 运行链路（CLI/Web UI）

1. `scripts/run_agent.py` 或 `scripts/serve_agent_ui.py` 启动
2. `agent_py/runner.py` 进入循环：`observe -> plan -> execute -> re-observe`
3. `agent_py/browser_runtime.py` 负责 Playwright/CDP 浏览器控制
4. `agent_py/planner.py` + `agent_py/llm_planner.py` 生成计划
5. `agent_py/safety.py` 进行高风险动作拦截与计划净化
6. `agent_py/executor.py` 执行动作
7. `agent_py/comparison.py` 等模块生成 artifact（比较、总结、抽取）

---

## 3. `agent_py/` 模块逐文件说明

## 3.1 `agent_py/web_app.py`

职责：

- Flask 应用入口
- 提供插件后端 API
- 提供本地 Web UI
- 保存推荐任务 JSON artifact

核心接口：

- `GET /api/extension/health`
  - 返回服务状态、LLM 环境配置状态、默认来源
- `POST /api/extension/plan`
  - 入参：`task`、`observation`、`settings`
  - 行为：推荐任务可强制 LLM；失败按策略返回 409
  - 出参：`plan`、`controller`、`llmStatus`、`source`
- `POST /api/extension/recommend`
  - 入参：`task`、`observation`、`execution`、可选 `memory`
  - 行为：先把请求上下文落盘到 `runs/recommendation/recommend-*.json`
  - 再调用 `recommend_from_observation` 产出结构化推荐
- `GET /`（Web UI）
  - 表单提交后直接调用 Runner 跑全流程
- `GET /download/trajectory.json`
  - 下载最近一次执行轨迹

内部关键函数：

- `_observation_from_extension`: 扩展 observation -> Python `Observation`
- `_task_mode`, `_is_recommendation_task`: 任务分类
- `_llm_failure_code`: LLM 失败码标准化
- `_persist_recommendation_payload`: 推荐任务 JSON 落盘

## 3.2 `agent_py/runner.py`

职责：

- 统一执行调度器（多轮循环）
- 轨迹记录与结果拼装
- 动作计划补全（保证最终有产物动作）

核心行为：

- 支持 `max_steps`
- 动作失败后按最新 observation 重规划
- 保留 execution trajectory（URL、动作、产物、错误）

## 3.3 `agent_py/browser_runtime.py`

职责：

- Playwright 浏览器运行时封装
- 优先 CDP 连接已有 Chrome（如 `http://127.0.0.1:9222`）
- 回退到临时 Chromium

核心能力：

- 打开 URL、点击、输入、滚动、按键、截图、等待
- 页面观测（可见元素、selector、label、bbox 等）
- 连接模式标注（`browserMode`、`connectionStatus`）

## 3.4 `agent_py/observer.py`

职责：

- 抽象观测结构构建
- 提取可交互元素、链接、卡片、表格、标题、价格、邮箱等

输出：

- `schema.Observation`

## 3.5 `agent_py/schema.py`

职责：

- 定义系统核心数据结构（强类型）

主要对象：

- `Element`
- `Observation`
- `Action`
- `Plan`
- `ActionResult`
- `ExecutionResult`

说明：

- 前后端交互统一走这些结构的 dict 序列化，减少字段漂移

## 3.6 `agent_py/planner.py`

职责：

- 规则规划器（Rule Planner）
- 对常见任务（搜索、填写、回复、分析、查找）生成稳定动作序列

特点：

- 可在 LLM 不可用时兜底
- 推荐任务在“LLM 强制模式”下不会使用该兜底

## 3.7 `agent_py/llm_planner.py`

职责：

- LLM 规划器
- 同时支持：
  - OpenAI-compatible `/chat/completions`
  - Gemini native `generateContent`（按配置自动判断通道）

关键点：

- `LLMConfig.from_env()` 从 `.env` 加载
- `request_text_completion` 统一请求入口
- 内置 `requests + retry`
- 解析并校验 LLM 返回 JSON 计划
- 失败时抛异常，由上层决定回退或中断

## 3.8 `agent_py/safety.py`

职责：

- 安全层（动作净化）

规则重点：

- 高风险动作（支付、删除、上传、权限等）拦截或转高亮
- 允许策略下可放行“普通提交/发送/发布”
- 校验 action type、targetId 合法性

## 3.9 `agent_py/executor.py`

职责：

- 执行动作并返回 `ActionResult`
- 与 Runtime 协作执行浏览器动作
- 生成抽取/总结/比较等 artifact

## 3.10 `agent_py/comparison.py`

职责：

- 候选项抽取、清洗、评分、比较、推荐输出

核心能力：

- `build_candidate_set`：汇总 cards/tables/memory 候选
- 去噪过滤（导航项、聚合壳）
- 规则比较 + LLM 比较两套路径
- `recommend_from_observation`：
  - 返回结构化结果：`comparisonTable`、`topPick`、`why`、`evidence`、`confidence`
  - 可设置 `require_llm=True` 强制 LLM 参与

## 3.11 `agent_py/memory.py`

职责：

- 任务执行记忆层

记忆内容：

- 搜索词、访问 URL、候选快照、详情页采样
- 多分支 worker 状态、合并日志、证据图

作用：

- 支撑跨页面比较与推荐
- 为 LLM 提供连续上下文

## 3.12 `agent_py/workflow.py`

职责：

- 生成工作流控制器对象（阶段、队列、分支、worker 可视化状态）
- 给前端展示“当前阶段 + 分支任务树”

## 3.13 `agent_py/config.py`

职责：

- 加载环境变量（含 `.env`）
- 提供统一配置入口

## 3.14 `agent_py/html_model.py`

职责：

- 页面文本/结构分析辅助模型（供观察与抽取逻辑复用）

## 3.15 `agent_py/__init__.py`

职责：

- 包初始化与导出

---

## 4. `scripts/` 后端脚本梳理

- `scripts/serve_agent_ui.py`
  - 启动 Flask 本地服务（默认 `127.0.0.1:8787`）
- `scripts/run_agent.py`
  - CLI 运行单任务
- `scripts/run_python_agent.py`
  - 兼容入口（历史脚本）
- `scripts/launch_chrome_cdp.py`
  - 启动可被 CDP 附着的 Chrome
- `scripts/run_real_browser_checks.py`
  - 回归与验收脚本
- `scripts/test_gemini.py`
  - Gemini 通道与模型连通性测试
- `scripts/serve_demo.py`
  - 本地 Demo 页面服务（用于自动化回归）

---

## 5. 配置体系

主要环境变量（`.env`）：

- `BROWSER_AGENT_API_BASE`
- `BROWSER_AGENT_API_KEY`
- `BROWSER_AGENT_MODEL`

默认行为：

- 后端优先读 `.env`
- 扩展默认不要求用户在 popup 手输 key/model（除非开启覆盖调试）

---

## 6. 数据产物与目录

- 执行轨迹：`trajectory.json`（Web UI 下载）
- 推荐 JSON 落盘目录：`runs/recommendation/`
- 截图目录：`runs/screenshots*`（按运行参数）

---

## 7. 测试梳理（后端相关）

关键测试文件：

- `tests/test_extension_api.py`
- `tests/test_llm_and_safety.py`
- `tests/test_python_agent.py`
- `tests/test_workflow_controller.py`
- `tests/test_real_world_skills.py`

覆盖重点：

- API 健康检查与计划接口
- 推荐任务 LLM 强制参与策略
- 安全拦截策略
- 规则/LLM 规划兼容
- 工作流控制器结构

---

## 8. 当前已知问题（面向你现在的使用场景）

1. 某些电商页面（如 JD）候选卡片提取仍会受动态加载与反爬结构影响，可能出现 `items=[]`。
2. 插件 content 注入和页面焦点约束可能导致 `copy` 或 `type` 间歇失败（已持续修复中）。
3. 第三方网关模型可用性波动会触发 LLM 失败；推荐任务在强制模式下会直接失败返回，而不是静默规则回退。

---

## 9. 后续建议（工程优先级）

P0：

- 增加“执行前后 observation 差分”日志，便于排查页面未真正变更问题
- 在推荐流程里强制“多页采样成功阈值”后再允许产出结论

P1：

- 把推荐任务拆成显式阶段对象持久化（intent/search/filter/sample/score/final）
- 增加候选商品结构化字段抽取器（价格、评分、销量、品牌、参数）

P2：

- 引入异步 worker 并发采样详情页（多 tab/context）
- 增加推荐任务专用评测集与成功率仪表板

---

## 10. 一句话总结

当前后端已经具备“真实浏览器控制 + 规划执行 + 安全控制 + 推荐落盘 + LLM 比对”的完整骨架；你下一步重点是增强电商页候选抽取鲁棒性和多页采样深度，这会直接决定“推荐质量”是否达到真实可用标准。
