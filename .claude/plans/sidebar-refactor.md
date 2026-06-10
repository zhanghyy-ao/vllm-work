# 实现计划：Chrome 扩展侧边栏重构 + 三大功能优化

## 项目现状

这是一个 Chrome 浏览器 Agent 扩展，通过 popup 弹窗交互，后端使用 Python (backend_api.py) 提供 LLM 规划能力。当前问题：
1. UI 是 popup 模式（440px 宽弹窗），用户离开即关闭
2. 缺少用户账户管理
3. 商品推荐流程中 LLM 没有返回有效推荐内容
4. GitHub 场景只做了搜索跳转，没有仓库内容识别和代码跳转

---

## 一、将 Popup 前端改为侧边栏 (Side Panel)

**改动文件：**
- `chrome_extension/manifest.json` — 添加 `side_panel` 配置
- `chrome_extension/sidepanel.html` — 新建（替代 popup.html 作为主界面）
- `chrome_extension/sidepanel.css` — 新建（适配侧边栏宽度和常驻布局）
- `chrome_extension/sidepanel.js` — 新建（复用 popup.js 逻辑，增加账户/GitHub 面板）
- `chrome_extension/background.js` — 添加 side panel 注册逻辑
- `chrome_extension/popup.html` — 简化为引导页，点击按钮打开侧边栏

**方案：**
- manifest.json 中声明 `"side_panel": { "default_path": "sidepanel.html" }`
- 添加 `"sidePanel"` 权限
- background.js 中用 `chrome.sidePanel.setOptions()` 控制 panel
- 侧边栏使用 tab 切换：**任务** | **账户** | **GitHub**
- 宽度自适应（侧边栏默认约 360px）

---

## 二、用户账户 JSON 管理

**改动文件：**
- `chrome_extension/sidepanel.js` — 账户 Tab 的 UI 逻辑
- `chrome_extension/sidepanel.html` — 账户管理面板 HTML
- 数据存储在 `chrome.storage.local` 中，key 为 `"user_accounts"`

**数据结构（JSON）：**
```json
{
  "user_accounts": [
    {
      "id": "uuid",
      "platform": "github",
      "platform_url": "https://github.com",
      "username": "user123",
      "password": "encrypted_or_stored",
      "display_name": "GitHub 账户",
      "extra_info": { "email": "...", "token": "..." },
      "created_at": "2026-06-09T..."
    }
  ]
}
```

**平台自动识别规则：**
- URL 包含 github.com → platform: "github"
- URL 包含 jd.com / tmall.com / taobao.com → platform: "shopping"
- URL 包含 bilibili.com / youtube.com → platform: "video"
- 用户指定账户名时，根据当前标签页 URL 或手动选择平台

**功能：**
- 添加/编辑/删除账户
- 指定某账户时自动匹配平台并高亮
- Agent 运行时可读取相关平台账户（不自动登录，仅标注身份）

---

## 三、商品推荐：修复 LLM 无返回问题

**根因分析：**

通过阅读代码链路：
1. `popup.js` → `background.js` (`controlBrowser`) → `fetchRunResult` (POST /api/run)
2. 后端 `backend_api.py` → `HarnessRuntime.run()` → `_run_workflow()`
3. `_run_workflow()` 调用 `plan_next_step()` → navigator LLM 规划 → dispatch_node 执行
4. 最后 `build_report_payload()` 调用 reporter LLM 生成 summary/recommendations

问题点：
- `build_agent_config(use_llm=True)` 在后端 `/api/run` 中传入 `use_llm=bool(payload.get("use_llm", False))`
- 前端确实传了 `use_llm: true`
- 但 reporter 的 LLM 调用依赖 `client.enabled`，如果 API key 缺失或模型返回格式不对就会静默失败
- 在 shopping 领域，reporter prompt 需要更明确的指令让模型返回 recommendations 数组

**修复方案：**
- `browser_agent/agents/reporter.py` — 增强 shopping 域的 reporter prompt，确保推荐列表在无证据时也返回基于规划的初步推荐
- `browser_agent/llm/agent.py` — 检查 reporter LLM 返回，增加 fallback 逻辑，当 recommendations 为空时从 evidence/candidates 自动聚合
- `browser_agent/output/report_builder.py` — 在 deterministic artifact 构建阶段，从 memory evidence 中提取商品候选作为 fallback recommendations
- `backend_api.py` — 增加更详细的 debug 日志，方便定位 LLM 返回空的原因

---

## 四、GitHub 仓库识别、内容整理与代码跳转

**改动文件：**
- `chrome_extension/sidepanel.js` — GitHub Tab 的 UI 逻辑
- `chrome_extension/sidepanel.html` — GitHub 面板 HTML
- `chrome_extension/background.js` — 添加 GitHub 页面解析消息处理
- `backend_api.py` — 添加 `/api/github/analyze` 端点
- `browser_agent/agents/github_agent.py` — 新建，GitHub 仓库分析 agent

**功能实现：**
1. **自动识别仓库**：侧边栏打开时检测当前 tab URL 是否为 github.com/{owner}/{repo}，如果是则自动触发分析
2. **仓库内容整理**：
   - 通过页面 DOM 抓取仓库的文件结构、README、Star/Fork/Issues 数量
   - 调用后端 LLM 生成仓库概要（技术栈、主要功能、代码结构）
3. **代码/函数跳转**：
   - 用户在侧边栏输入函数名或代码片段
   - 后端通过 GitHub API（或页面内搜索）定位到具体文件和行号
   - 自动导航浏览器标签页到对应 URL（github.com/{owner}/{repo}/blob/main/path#L42）

---

## 实现顺序

1. **Phase 1**: manifest.json + sidepanel 基础框架（HTML/CSS/JS Tab 切换）
2. **Phase 2**: 迁移 popup.js 核心逻辑到 sidepanel.js（任务 Tab）
3. **Phase 3**: 账户管理 Tab 实现
4. **Phase 4**: 修复商品推荐 LLM 返回问题
5. **Phase 5**: GitHub Tab + 仓库识别和代码跳转
6. **Phase 6**: 简化 popup.html 为开启侧边栏的引导页

---

## 技术决策

- 密码存储：使用 `chrome.storage.local`，生产环境应使用加密存储，当前 MVP 阶段明文存储并提示用户
- 侧边栏保持常驻，不像 popup 会自动关闭
- GitHub API 调用：优先使用页面 DOM 信息（无需 token），备选方案通过用户配置的 GitHub token 调用 API
- 前端不引入额外框架，保持原生 JS + CSS 风格
