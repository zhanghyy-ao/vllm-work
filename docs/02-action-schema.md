# Action Schema

所有 Planner 输出都必须转成结构化动作，Executor 只执行 schema 内的动作。这样可以避免模型输出任意 JavaScript，提高安全性和可测试性。

## Observation

```json
{
  "url": "http://localhost:8765",
  "title": "Browser Agent Demo",
  "text": "visible page text...",
  "elements": [
    {
      "id": "e12",
      "tag": "input",
      "role": "textbox",
      "label": "搜索主题",
      "type": "search",
      "placeholder": "输入主题，例如 多模态大模型",
      "text": "",
      "rect": { "x": 120, "y": 240, "width": 420, "height": 40 }
    }
  ]
}
```

## Plan

```json
{
  "summary": "在搜索框中搜索多模态大模型并打开结果",
  "confidence": 0.82,
  "actions": [
    {
      "type": "type",
      "targetId": "e12",
      "value": "多模态大模型",
      "reason": "搜索框与主题输入最匹配"
    },
    {
      "type": "press",
      "targetId": "e12",
      "key": "Enter",
      "reason": "提交搜索"
    }
  ]
}
```

## 支持动作

- `highlight`：高亮元素，仅用于预览。
- `click`：点击目标元素。
- `type`：清空并输入文本。
- `press`：向目标元素发送键盘事件，例如 `Enter`。
- `scroll`：页面滚动。
- `navigate`：跳转到 URL。
- `extract`：从页面提取包含关键词的文本。
- `summarize`：总结当前页面可见内容。
- `collect`：结构化抽取链接、邮箱、价格或结果卡片。
- `compare`：比较页面中的结果卡片或商品卡片。
- `brief`：根据页面类型生成真实场景简报，如搜索结果、GitHub 仓库、文档页。
- `find`：在当前页面中查找关键词，返回相关文本片段和可操作元素。
- `copy`：复制上一轮提取或比较结果到剪贴板。
- `wait`：等待页面加载或动态内容变化。

## 高风险动作

以下动作默认只生成草稿或要求用户二次确认：

- 提交真实表单。
- 发送消息、邮件、评论。
- 删除、支付、下单、发布。
- 上传隐私文件或导出敏感信息。

第一版 Demo 中，消息回复会填入输入框并高亮“发送”按钮，但不会自动点击发送按钮。
