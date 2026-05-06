# LLM/VLM Planner 接入设计

第一版 Demo 使用规则 Planner 保底，后续可以替换为真实大模型 Planner。为了避免重写插件，模型只需要遵守 `Observation -> Plan` 接口。

## 输入

```json
{
  "task": "填写 姓名=张三 邮箱=zhangsan@example.com",
  "observation": {
    "url": "...",
    "title": "...",
    "text": "...",
    "elements": [
      {
        "id": "e1",
        "tag": "input",
        "role": "textbox",
        "label": "姓名",
        "placeholder": "请输入姓名",
        "rect": { "x": 100, "y": 200, "width": 320, "height": 42 }
      }
    ]
  }
}
```

## 输出

```json
{
  "summary": "填写表单草稿",
  "confidence": 0.86,
  "warnings": ["不自动提交表单"],
  "actions": [
    {
      "type": "type",
      "targetId": "e1",
      "value": "张三",
      "reason": "姓名字段与用户指令匹配"
    }
  ]
}
```

## 推荐 Prompt

```text
你是一个浏览器辅助操作智能体。你只能输出 JSON，不允许输出解释性自然语言。

任务：{task}

网页观测：
{observation}

请生成一个安全、可解释、可执行的动作计划。

规则：
1. 只能使用 action schema 中允许的动作：highlight, click, type, press, scroll, navigate, extract, summarize, collect, compare, brief, find, copy, wait。
2. 不要执行付款、删除、发布、提交、发送等高风险最终确认动作。
3. 如果需要发送消息或提交表单，只能填写草稿并 highlight 按钮。
4. targetId 必须来自 observation.elements。
5. 每个动作必须写 reason。
```

## 模型选择

- 低成本文本 Planner：Qwen/Qwen2.5、GPT-4o-mini、Gemini Flash 等，输入 DOM 元素表。
- 多模态 Planner：Qwen2.5-VL、GPT-4o、Gemini Pro Vision 等，输入截图 + DOM 元素表。
- 本地保底：规则 Planner 继续作为 fallback，当模型输出 JSON 校验失败时启用。

## 工程接入位置

- 规则入口：`extension/planner.js` 的 `planTask(command, observation)`。
- 模型入口：`extension/model_planner.js` 的 `planTaskWithModel(command, observation, settings)`。
- 配置位置：插件 Popup 中的 `LLM Planner 设置（可选）`，从 `chrome.storage.local` 读取 API Base、API Key 和模型名。
- 输出必须先经过 schema 校验，再交给 `content.js` 执行。

## 回退机制

如果模型请求失败、输出不是 JSON、动作类型不在白名单中，插件会自动回退到本地规则 Planner，并把失败原因写入 `warnings`。这样 Demo 在没有 API Key 或网络不稳定时仍然可用。
