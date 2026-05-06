# SYSU Python Browser Agent

这是一个面向“网页多模态 Agent / 浏览器辅助操作系统”课程项目的 Python-only 真实浏览器 Agent。核心路径使用 Python Playwright 控制浏览器、Python Planner/LLM 规划动作、Python Flask 提供本地 Web UI。

当前仓库版本：`v0.1.0`

版本记录见 [CHANGELOG.md](/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/CHANGELOG.md)，后续路线见 [docs/08-version-roadmap.md](/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/docs/08-version-roadmap.md)。

## 已实现功能

- Python Playwright 控制真实 Chrome/Chromium 浏览器，默认优先连接 Chrome CDP。
- Python 规则 Planner + OpenAI-compatible LLM Planner。
- 页面观测：采集 URL、标题、文本、可交互元素、稳定 selector、表单/section 上下文、可见性、可用性、bbox、链接、卡片、表格、邮箱、价格和截图路径。
- 动作执行：支持 `type`、`click`、`press`、`highlight`、`navigate`、`extract`、`summarize`、`collect`、`compare`、`brief`、`find`、`copy`。
- 安全策略：普通搜索提交不拦截；显式允许后可执行普通提交/发送/发布；删除、支付、上传、下单、验证码、权限授权等硬风险仍强制转为 `highlight`。
- 多轮执行：每步执行后重新观察页面，动作失败时会基于最新页面自动重规划，避免动态页面或跳转后的旧 targetId 直接卡死。
- 本地 Flask Web UI 和 CLI。
- 轨迹日志导出为 `trajectory.json`。

## 快速运行

1. 安装依赖：

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

2. 启动测试站：

```bash
python3 scripts/serve_demo.py
```

3. 使用 CLI 运行 Agent：

```bash
python3 scripts/run_agent.py --url http://127.0.0.1:8765 --task "搜索 多模态大模型"
```

默认会打开一个可见 Chromium，慢动作执行，并在运行结束后停留几秒，方便录屏和肉眼确认。若需要后台运行再加 `--headless`。

如果希望 Agent 操控你已经打开的 Chrome，而不是临时启动一个 Chromium，可以先用远程调试端口启动 Chrome：

```bash
python3 scripts/launch_chrome_cdp.py --url http://127.0.0.1:8765
```

这个脚本使用独立 profile，不会污染你的主浏览器；如果找不到系统 Chrome，会自动尝试 Playwright 安装的 Chromium。想让自动验收使用后台浏览器可加 `--headless`。

然后运行：

```bash
python3 scripts/run_agent.py \
  --url http://127.0.0.1:8765 \
  --task "搜索 多模态大模型" \
  --cdp-url http://127.0.0.1:9222
```

如果 `http://127.0.0.1:9222` 没有启动，系统会自动回退到临时 Chromium，并在 trajectory 中写入 `browserMode` 和 `connectionStatus`。

4. 或启动本地 Web UI：

```bash
python3 scripts/serve_agent_ui.py
```

然后打开：

```text
http://127.0.0.1:8787
```

5. 常用指令：

```text
搜索 多模态大模型
填写 姓名=张三 邮箱=zhangsan@example.com 主题=多模态智能体 备注=这是课程 Demo
回复小明：我今晚八点前把材料发你
总结当前页面
提取页面链接和邮箱
比较这些浏览器智能体方案
```

## 功能模块

- `辅助搜索`：识别搜索框，输入主题，提交搜索并提取相关片段。
- `表单填写`：从 `字段=值` 指令中解析字段，自动匹配 label/placeholder/name。
- `消息回复`：填入回复草稿并高亮发送按钮，不自动发送。
- `页面总结`：基于当前页面可见文本生成 3--6 条要点。
- `结构化抽取`：抽取链接、邮箱、价格、表格或结果卡片，输出 JSON。
- `结果比较`：对页面卡片按相关性、评分、内容密度进行简单排序。
- `界面分析`：统计页面控件、推断工作流、标出需要谨慎确认的按钮。
- `项目分析`：提取页面结构、候选模块、关键资源链接和可复用性判断。
- `页面查找`：在当前页面查找关键词，返回相关片段和可操作元素。
- `复制结果`：摘要、抽取和比较结果会自动复制到剪贴板。

## 现实网页模式

本地测试站只是回归测试用的“靶场”。真实使用时，启动 Web UI 后把 `URL` 改成任意网页地址，再输入下面这类指令：

```text
研究当前页面
分析这个 GitHub 仓库
在文档中找 安装 配置 API
总结当前页面
提取页面链接和邮箱
填写 name=Alice email=alice@example.com message=Please send me the demo link
分析这个界面能做什么
分析这个项目的可复用性
帮忙查找 browser harness
```

当前实现包含几类 real-world skills：

- `研究/搜索助手`：适用于搜索结果页、资料列表页、博客列表页，输出来源列表和下一步建议。
- `GitHub 仓库理解`：适用于 GitHub repo 页面，提取 README/安装/License/Issues 等工程线索。
- `文档站助手`：适用于技术文档和教程页，提取安装、配置、API key、代码命令等片段。
- `通用表单草稿`：适用于联系表单、问卷、评论框，只填写草稿并高亮提交按钮。
- `界面分析`：适用于陌生网站，先判断这个页面有什么输入框、按钮、链接和潜在风险动作。
- `项目分析`：适用于项目页、产品页、论文项目主页，输出可复用模块、关键资源和下一步建议。
- `页面查找`：适用于长文档或复杂页面，定位关键词相关片段和可操作元素。

## LLM Planner（可选）

默认使用本地规则 Planner，不需要 API Key。若希望让 LLM 根据页面状态生成更灵活的动作计划：

CLI：

```bash
python3 scripts/run_agent.py \
  --url https://github.com/browser-use/browser-harness \
  --task "分析这个 GitHub 仓库" \
  --api-base https://api.openai.com/v1 \
  --api-key "$OPENAI_API_KEY" \
  --model gpt-4o-mini
```

Web UI：在页面中填写 `API Base`、`API Key` 和 `Model`。如果要控制已打开的 Chrome，把 `Chrome CDP URL` 填成 `http://127.0.0.1:9222`；否则系统会打开一个临时 Chromium，并按 `可视化慢动作` 和 `运行后停留秒数` 展示执行过程。`允许显式提交/发送` 只放开普通提交、发送、发布；付款、删除、上传、验证码、权限授权等仍会被拦截。

兼容 OpenAI 风格 `/chat/completions` 接口。模型输出会经过动作白名单过滤；如果请求失败或 JSON 解析失败，会自动回退到本地规则 Planner。

Synai996 示例配置可以写入 `.env`：

```bash
BROWSER_AGENT_API_BASE=https://synai996.space/v1
BROWSER_AGENT_MODEL=gemini-3.1-pro-low
BROWSER_AGENT_API_KEY=你的 API Key
```

如果第三方网关返回 `model_not_found`、`quota` 或空响应，系统会保留本地规则 Planner 的可用 Demo，不会中断任务。

安全边界保持不变：不会自动发送消息、提交表单、付款、删除、发布或上传文件。

## 测试

运行完整 Python 测试：

```bash
python3 -m unittest discover -s tests -v
```

CLI 验收：

```bash
python3 scripts/run_agent.py --url http://127.0.0.1:8765 --task "分析这个界面能做什么" --headless
```

当前测试覆盖本地 Demo 页和真实网页模拟场景：搜索结果页、GitHub 仓库页、文档页、英文联系表单页、界面分析、项目分析和页面查找。

真实 CDP 浏览器验收：

```bash
python3 scripts/run_real_browser_checks.py
```

该脚本会启动 demo site、启动一个带 CDP 的独立 Chromium，并依次验证搜索、填表、回复草稿、界面分析、比较、抽取、页面查找和打开链接 8 个任务。所有 trajectory 会写入 `runs/real-browser-checks/`，并要求 `browserMode=cdp-attached` 且 artifact 非空。需要肉眼观察真实浏览器动作时加 `--headed`。

## 工程文档

- `docs/00-repo-research.md`：GitHub 调研与取舍。
- `docs/01-architecture.md`：系统架构。
- `docs/02-action-schema.md`：动作协议。
- `docs/03-skills.md`：功能模块拆分。
- `docs/04-evaluation.md`：评测方案。
- `docs/07-product-requirements-document.md`：完整 PRD。
- `docs/08-version-roadmap.md`：版本迭代规划。

## 后续路线

- 扩大批量评测任务集，统计更多真实网页任务成功率。
- 给课程网站、GitHub、问卷页面等沉淀 domain skills。
- 旧 `extension/` 目录保留为历史参考，不再是主实现路径。
