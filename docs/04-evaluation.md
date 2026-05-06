# 评测方案

## 课程验收对齐

课程大作业中网页 Agent 方向要求：

- 选择 1--2 个真实网站。
- 每个网站至少 3 个任务场景。
- 每个场景至少 10 次独立测试。
- 总测试次数不少于 60 次。
- 统计成功率并分类失败类型。

## 第一阶段：本地可控测试

使用 `demo-site/index.html` 覆盖三类任务：

- 辅助搜索：搜索“多模态大模型”“浏览器智能体”等主题。
- 表单填写：填写姓名、邮箱、主题、备注。
- 消息回复：生成回复草稿并高亮发送按钮。

目标是验证插件链路、动作 schema 和日志记录。

## 第二阶段：真实网页测试

候选网站：

- 课程网站或本地教学资源页。
- GitHub 仓库搜索和 issue 页面。
- 文档站点，例如 Playwright、Qwen、LangChain 文档。

真实网站只做低风险任务，例如搜索、筛选、复制信息、填写草稿，不自动发送或提交。

## 指标

- `Task Success Rate`：任务完整成功比例。
- `Step Accuracy`：单步动作是否合理。
- `Element Grounding Accuracy`：点击/输入是否命中正确元素。
- `Average Steps`：平均动作步数。
- `Safety Intervention Count`：安全拦截或二次确认次数。
- `Failure Type`：识别失败、规划失败、执行失败、页面变化失败、安全拦截。

## 轨迹格式

```json
{
  "task": "搜索多模态大模型",
  "url": "http://localhost:8765",
  "actions": [
    {
      "type": "type",
      "targetId": "e3",
      "ok": true,
      "reason": "搜索框匹配",
      "timestamp": "2026-05-05T15:10:00.000Z"
    }
  ],
  "finalStatus": "success"
}
```
