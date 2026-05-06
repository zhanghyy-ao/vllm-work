# Python Browser Agent PRD

## 1. 文档信息

- 产品名称：`Python Browser Agent`
- 产品形态：`Python-only 浏览器辅助操作智能体`
- 文档版本：`v1.0`
- 文档状态：`课程项目版 PRD`
- 目标读者：`项目成员、课程老师、评测人员、后续开发者`

## 2. 产品概述

`Python Browser Agent` 是一个面向浏览器辅助操作场景的真实可用智能体系统。用户通过自然语言输入任务，系统连接真实 Chrome/Chromium 浏览器，观察当前页面状态，生成动作计划，执行点击/输入/导航/提取/总结等动作，并输出可验证结果与完整轨迹。

该项目的核心特点不是“会点按钮”，而是把浏览器智能体工程化：支持真实浏览器连接、页面结构化观测、规则与 LLM 双 Planner、多轮执行与失败重规划、安全拦截、轨迹导出、本地 Web UI、CLI 和自动化验收。

## 3. 背景与问题

当前常见浏览器 Agent Demo 往往存在几个问题：

- 只能在 toy 页面中工作，无法真正连接用户浏览器。
- 元素定位不稳定，容易误点、误填、跨表单匹配错误。
- 只有“单轮计划”，页面变化后无法自动纠错。
- 只会执行动作，不会产出结构化结果或摘要，难以形成课程报告里的“任务闭环”。
- 缺少安全策略，容易把发送、提交、支付等高风险动作直接执行。

本项目希望解决以上问题，构建一个“可展示、可测试、可扩展、可报告”的课程级浏览器智能体系统。

## 4. 产品目标

### 4.1 总体目标

构建一个以 Python 为核心实现的真实浏览器智能体系统，能够在低风险网页任务中稳定完成搜索、查找、表单草稿填写、内容提取、页面分析、项目分析、文档检索和结果比较等工作。

### 4.2 具体目标

- 支持连接用户已启动的 Chrome CDP，真正操控真实浏览器页面。
- 提供规则 Planner 和 OpenAI-compatible LLM Planner 双路径，保证在 LLM 不稳定时仍可运行。
- 支持多轮 `observe -> plan -> execute -> observe` 执行闭环，并在动作失败后自动重规划。
- 所有任务都能产出 `artifact`，例如摘要、JSON、简报、查找结果。
- 对高风险动作进行安全拦截，不自动执行支付、删除、上传、授权、验证码等操作。
- 提供本地 Web UI、CLI、轨迹 JSON、截图和自动化测试，满足课程展示与报告需要。

### 4.3 非目标

- 不做跨账号登录与验证码绕过。
- 不自动完成支付、下单、删除、上传文件、权限授权等高风险操作。
- 不追求在所有任意网页上完全无人值守。
- 不以浏览器扩展作为主交付路径，扩展目录只保留为历史参考。

## 5. 目标用户

### 5.1 主要用户

- 课程项目开发者：需要一个可复现实验平台和报告支撑材料。
- 课程老师/评测者：需要看到真实浏览器控制、日志、指标和结果闭环。
- 普通演示用户：希望输入一句自然语言，就能让浏览器帮助完成低风险任务。

### 5.2 用户特征

- 具备基本网页使用能力，但不一定懂浏览器自动化技术。
- 关注“是否真的在操控浏览器”和“是否有现实价值”。
- 需要可视化、可解释、可回放的执行结果。

## 6. 典型使用场景

### 6.1 场景 A：搜索与研究

用户输入“搜索 多模态大模型”或“研究当前页面”，Agent 在页面内搜索或跳转搜索引擎，提取相关结果，输出研究摘要和来源信息。

### 6.2 场景 B：文档检索

用户打开技术文档页面，输入“在文档中找 安装 配置 API”，Agent 提取相关片段并整理成简短文档简报。

### 6.3 场景 C：GitHub 项目分析

用户打开 GitHub 仓库后输入“分析这个 GitHub 仓库”或“分析这个项目的可复用性”，Agent 提取 README、安装线索、关键资源链接、工程判断和风险。

### 6.4 场景 D：表单填写草稿

用户输入“填写 姓名=张三 邮箱=xxx 主题=多模态智能体 备注=这是课程 Demo”，Agent 自动匹配字段并填写，但默认只高亮提交按钮，不自动提交。

### 6.5 场景 E：回复消息草稿

用户输入“回复小明：我今晚八点前把材料发你”，Agent 找到消息输入区域并填入草稿，同时高亮发送按钮，等待用户确认。

### 6.6 场景 F：陌生网页分析

用户输入“分析这个界面能做什么”，Agent 统计页面输入框、按钮、链接、风险操作和可能工作流，输出界面分析报告。

## 7. 产品范围

### 7.1 本期范围

- 真实浏览器控制
- 页面观测
- 规则 Planner
- LLM Planner
- 动作执行器
- 安全策略
- Web UI
- CLI
- 轨迹日志
- 自动评测
- Demo 站点与真实网页低风险任务支持

### 7.2 后续范围

- 更多领域技能沉淀
- 更高质量的跨站点任务评测
- 更完善的连续多轮任务管理
- 更强的页面结构感知与跨页面记忆

## 8. 功能清单

### 8.1 浏览器连接与运行时

#### 功能说明

系统优先通过 Chrome CDP 连接用户已打开的 Chrome；若未连接成功，则自动回退到临时 Playwright Chromium。

#### 需求点

- 默认支持 `http://127.0.0.1:9222`
- 支持独立 profile 启动远程调试 Chrome
- UI 和 trajectory 中展示 `browserMode` 与 `connectionStatus`
- CDP 模式下断开连接时不关闭用户主浏览器

#### 成功标准

- 用户可看到真实浏览器被操控
- 轨迹中明确记录当前是否为 `cdp-attached`

### 8.2 页面观测

#### 功能说明

系统需要在每轮执行前后采集页面状态，为规划与执行提供 grounding。

#### 观测内容

- URL
- 标题
- 页面文本
- headings
- links
- cards
- tables
- emails
- prices
- screenshot path
- viewport
- elements 列表

#### 元素字段

- `id`
- `tag`
- `selector`
- `role`
- `type`
- `name`
- `label`
- `text`
- `placeholder`
- `href`
- `value`
- `formId`
- `sectionLabel`
- `visible`
- `enabled`
- `bbox`

#### 成功标准

- Planner 能够基于观测结果稳定定位搜索框、按钮、表单字段和链接
- 不再依赖全页面简单顺序编号作为主要定位策略

### 8.3 Planner 系统

#### 功能说明

Planner 将用户自然语言任务转换为浏览器动作计划。

#### 组成

- 规则 Planner
- LLM Planner
- Planner 输出校验与 sanitize

#### 动作类型

- `highlight`
- `click`
- `type`
- `press`
- `scroll`
- `navigate`
- `extract`
- `summarize`
- `collect`
- `compare`
- `brief`
- `find`
- `copy`
- `wait`

#### 规划原则

- 优先选择可见且可操作元素
- 表单字段匹配必须参考 `formId/sectionLabel`
- 链接点击优先 exact text/label/href
- 任务必须有结果产物，不允许只做动作无输出
- LLM 失败时自动回退规则 Planner

### 8.4 多轮执行与纠错

#### 功能说明

系统执行不是单次静态计划，而是执行后重新观察页面，并在失败时自动重规划。

#### 需求点

- 每步后重新 observe
- 动作失败后基于最新页面重规划
- 页面跳转、元素过期、布局变化时自动纠错
- 达到 `max_steps` 后停止并记录告警

#### 成功标准

- 动态页面中任务不会因单个旧 targetId 直接中断
- 失败轨迹中可看到 `fallbackReason` 和 replan 信息

### 8.5 安全策略

#### 功能说明

系统必须对高风险动作进行保护，防止错误操作造成真实后果。

#### 安全策略

- 普通搜索提交不拦截
- 用户显式允许时，可执行普通提交/发送/发布
- 付款、删除、上传、下单、密码、验证码、权限授权等动作仍强制高亮确认
- 默认不自动发送消息和提交表单

#### 成功标准

- 安全拦截必须可解释
- 被拦截动作在 trajectory 中保留原始原因和替代动作

### 8.6 任务技能层

#### Skill 1：辅助搜索

- 支持页面内搜索
- 无搜索框时可跳转搜索引擎
- 搜索后自动提取结果摘要

#### Skill 2：表单填写

- 支持中英文 `字段=值`
- 自动匹配 input/textarea
- 默认只填写草稿，不自动提交

#### Skill 3：消息回复

- 识别消息输入区域
- 填写回复草稿
- 高亮发送按钮

#### Skill 4：页面总结

- 总结当前页面要点
- 输出可复制 artifact

#### Skill 5：结构化抽取

- 提取链接
- 提取邮箱
- 提取价格
- 提取表格
- 提取结果卡片

#### Skill 6：结果比较

- 对页面中的候选结果进行排序和推荐

#### Skill 7：界面分析

- 统计页面可交互元素
- 推断主要工作流
- 标出风险按钮

#### Skill 8：项目分析

- 识别项目结构与可复用模块
- 提取关键资源链接
- 给出工程复用建议

#### Skill 9：页面查找

- 查找关键词相关片段
- 定位相关元素
- 输出查找结果

#### Skill 10：文档助手

- 在文档页中提取安装、配置、API 线索
- 生成简短文档简报

#### Skill 11：GitHub 仓库理解

- 提取仓库用途
- 提取安装与运行线索
- 提取资源链接与工程风险

#### Skill 12：研究简报

- 针对搜索结果页、资料页、博客列表页生成研究型输出

### 8.7 结果产物与复制

#### 功能说明

每类任务必须生成可展示结果，不允许“执行了动作但没有结果”。

#### 结果类型

- 页面摘要
- JSON 抽取结果
- 比较结果
- 文档简报
- GitHub 项目简报
- 页面查找结果

#### 成功标准

- `execution.artifact` 非空
- 用户可通过 `copy` 动作或 UI 直接获取结果

### 8.8 本地 Web UI

#### 功能说明

Web UI 作为课程演示主入口，为用户提供无需命令行的操作界面。

#### 页面字段

- URL
- Task
- API Base
- Model
- API Key
- Chrome CDP URL
- Max Steps
- Screenshot Dir
- Slow Mo
- Linger
- Headless
- Allow Explicit Submit

#### 展示内容

- CDP 检测状态
- Artifact
- Browser Mode
- Connection Status
- Final URL
- Screenshots
- Trajectory JSON
- 导出按钮

#### 成功标准

- 用户可在一个页面内完成配置、执行、查看结果和导出轨迹

### 8.9 CLI

#### 功能说明

CLI 用于开发调试、批量运行和自动化验收。

#### 核心命令

```bash
python3 scripts/run_agent.py --url URL --task "任务"
python3 scripts/launch_chrome_cdp.py --url URL
python3 scripts/serve_agent_ui.py
python3 scripts/run_real_browser_checks.py
```

#### 成功标准

- 开发者可以用 CLI 完成启动、连接、执行与验收全流程

### 8.10 轨迹与日志

#### 功能说明

系统需要记录每步动作与页面状态，供课程汇报、失败分析和评测使用。

#### 日志内容

- task
- plan
- plannerSource
- browserMode
- connectionStatus
- warnings
- execution.ok
- execution.url
- execution.artifact
- trajectory

#### trajectory 单步内容

- action
- ok/error
- output
- url
- artifact
- observation summary
- fallbackReason
- replan

#### 成功标准

- 每次执行都可导出 `trajectory.json`
- 轨迹足以重建任务执行过程

### 8.11 自动测试与验收

#### 功能说明

系统需要具备可重复的单元测试、集成测试和真实浏览器验收能力。

#### 测试层级

- 单元测试
- 规则与安全测试
- 真实网页模拟测试
- 真实 CDP 浏览器端到端测试

#### 当前验收重点

- 搜索
- 填表
- 回复草稿
- 界面分析
- 比较
- 抽取
- 页面查找
- 打开链接

## 9. 用户流程

### 9.1 标准流程

1. 用户打开 Web UI 或 CLI。
2. 输入目标 URL 和任务。
3. 系统连接 Chrome CDP 或启动临时 Chromium。
4. Observer 采集页面状态。
5. Planner 生成动作计划。
6. Safety Policy 过滤或拦截高风险动作。
7. Executor 执行动作。
8. 系统重新观察页面，必要时继续执行或重规划。
9. 输出 artifact、截图和 trajectory。

### 9.2 高风险流程

1. 用户输入可能触发发送/提交/支付的任务。
2. Planner 识别相关动作。
3. Safety 将动作转换为 `highlight` 或要求确认。
4. 用户肉眼确认后再决定是否继续。

## 10. 非功能需求

### 10.1 稳定性

- 在本地 demo 页中稳定完成核心任务
- LLM 不可用时仍可使用规则 Planner

### 10.2 可解释性

- 每个动作必须包含 `reason`
- 每次拦截必须有说明

### 10.3 可测性

- 所有关键模块都可通过自动测试验证
- 支持批量真实浏览器检查

### 10.4 可扩展性

- 新增 skill 不应破坏既有 action schema
- 可逐步扩展为更多真实网站 domain skills

### 10.5 可演示性

- 支持 slow motion
- 支持 headed 模式
- 支持截图与轨迹导出

## 11. 指标设计

### 11.1 产品指标

- 任务成功率
- 单步动作准确率
- 元素定位准确率
- 平均步骤数
- 安全拦截次数
- artifact 非空率

### 11.2 课程评测指标

- 真实网站数量
- 每站任务场景数量
- 每任务重复测试次数
- 总测试次数
- 各失败类型占比

## 12. 验收标准

### 12.1 功能验收

- 支持真实 Chrome CDP 控制
- 支持 CLI 与 Web UI 双入口
- 支持核心 10+ skills
- 任务结束后必须有 artifact
- 轨迹可导出

### 12.2 测试验收

- 单元测试全部通过
- 真实浏览器 8 个基础任务全部通过
- `browserMode=cdp-attached`
- 高风险动作不被直接执行

### 12.3 展示验收

- 用户能肉眼看到浏览器被操控
- Web UI 中可见结果、状态、轨迹和截图

## 13. 风险与约束

### 13.1 技术风险

- 真实网页结构变化会导致元素定位失效
- 第三方 LLM 网关不稳定可能导致规划失败
- Chrome CDP 环境与本机浏览器配置存在差异

### 13.2 安全风险

- 如果安全策略不严，可能误触真实发送/提交动作
- 页面 prompt injection 可能误导模型规划

### 13.3 项目约束

- 核心逻辑必须尽量保持 Python 实现
- 不处理登录绕过、验证码、支付下单等高风险场景

## 14. 版本规划

### v1.0

- Python-only 核心架构
- 真实 Chrome CDP 控制
- 基础技能集合
- Web UI + CLI
- 轨迹导出
- 自动验收

### v1.1

- 增加更多真实网站 domain skills
- 增强多轮任务连续执行能力
- 扩展批量评测脚本

### v1.2

- 更强的页面理解与结果组织能力
- 更细粒度的用户确认与人机协同

## 15. 附录：当前实现对应关系

### 核心代码

- `agent_py/browser_runtime.py`：浏览器控制与页面观测
- `agent_py/planner.py`：规则 Planner
- `agent_py/llm_planner.py`：LLM Planner
- `agent_py/safety.py`：安全校验
- `agent_py/runner.py`：多轮执行与轨迹记录
- `agent_py/web_app.py`：本地 Web UI

### 脚本入口

- `scripts/run_agent.py`
- `scripts/launch_chrome_cdp.py`
- `scripts/serve_agent_ui.py`
- `scripts/run_real_browser_checks.py`

### 测试

- `tests/test_python_agent.py`
- `tests/test_llm_and_safety.py`
- `tests/test_real_world_skills.py`

