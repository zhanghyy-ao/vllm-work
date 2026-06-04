# Multi-Scenario Certification - 2026-06-03

## Scope

Re-run representative browser-agent scenarios on the current codebase and summarize execution quality, evidence collection, and report completeness.

## Scenario Results

| Scenario | OK | Steps | Events | Evidence | Recommendations | Comparison Rows | Summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| shopping | True | 3 | 3 | 9 | 3 | 3 | Workflow 'shopping_workflow' completed for '推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论'. Collected 5 candidate links and 9 evidence items. |
| github | True | 3 | 3 | 9 | 3 | 3 | Workflow 'github_research' completed for '帮我找几个可以参考的浏览器自动化智能体 GitHub 开源项目，比较活跃度、语言、README质量和适合借鉴的实现点'. Collected 5 candidate links and 9 evidence items. |
| video | True | 3 | 3 | 5 | 1 | 1 | Workflow 'video_workflow' completed for '帮我查找并整理一个 CLIP 多模态模型入门教程视频的主要内容'. Collected 3 candidate links and 5 evidence items. |

## Current Run Files

- `shopping`: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/latest-run-shopping-current.json`
- `github`: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/latest-run-github-current.json`
- `video`: `/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/latest-run-video-current.json`

## Interpretation

- `shopping` now passes on the current codebase and collects marketplace-oriented evidence.
- `github` passes and produces repository comparison evidence suitable for implementation reference research.
- `video` passes and produces tutorial-style evidence and summarization output.

## Raw JSON

```json
{
  "generated_at": "2026-06-04T00:05:47.600869",
  "scenarios": [
    {
      "name": "shopping",
      "ok": true,
      "goal": "推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论",
      "summary": "Workflow 'shopping_workflow' completed for '推荐1000元以内适合通勤和办公的降噪耳机，需要比较商城商品页、专业测评、用户评论差评、视频测评评论后给出结论'. Collected 5 candidate links and 9 evidence items.",
      "steps": 3,
      "events": 3,
      "evidence_items": 9,
      "recommendations": 3,
      "comparison_rows": 3,
      "next_actions": 1,
      "result_path": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/latest-run-shopping-current.json"
    },
    {
      "name": "github",
      "ok": true,
      "goal": "帮我找几个可以参考的浏览器自动化智能体 GitHub 开源项目，比较活跃度、语言、README质量和适合借鉴的实现点",
      "summary": "Workflow 'github_research' completed for '帮我找几个可以参考的浏览器自动化智能体 GitHub 开源项目，比较活跃度、语言、README质量和适合借鉴的实现点'. Collected 5 candidate links and 9 evidence items.",
      "steps": 3,
      "events": 3,
      "evidence_items": 9,
      "recommendations": 3,
      "comparison_rows": 3,
      "next_actions": 1,
      "result_path": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/latest-run-github-current.json"
    },
    {
      "name": "video",
      "ok": true,
      "goal": "帮我查找并整理一个 CLIP 多模态模型入门教程视频的主要内容",
      "summary": "Workflow 'video_workflow' completed for '帮我查找并整理一个 CLIP 多模态模型入门教程视频的主要内容'. Collected 3 candidate links and 5 evidence items.",
      "steps": 3,
      "events": 3,
      "evidence_items": 5,
      "recommendations": 1,
      "comparison_rows": 1,
      "next_actions": 1,
      "result_path": "/Users/zhanghyy-ao/Desktop/课程材料/多模态/vllm-work/runs/latest-run-video-current.json"
    }
  ]
}
```