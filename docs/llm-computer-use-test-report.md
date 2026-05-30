# 多场景 LLM 智能体测试报告（Computer Use + DeepSeek）

- 测试时间: 2026-05-28 10:57:05
- 测试模型: `deepseek-chat`
- 测试模式: `--use-llm`
- 浏览器可视化核验: 已使用 `@电脑` 在 Chrome 打开各场景落地页

## 场景结果总览

| 场景 | 总体ok | 步骤通过 | evidence条数 | report缺失字段 | 结果文件 |
|---|---:|---:|---:|---|---|
| github | True | 4/4 | 10 | 无 | `runs/latest-run-github-llm.json` |
| paper | True | 4/4 | 13 | 无 | `runs/latest-run-paper-llm.json` |
| shopping | True | 4/4 | 13 | recommendations | `runs/latest-run-shopping-llm.json` |

## Computer Use 可视化核验记录

通过 `@电脑` 在 `Google Chrome` 中逐项打开并确认页面可达：
- `github`: `https://github.com/search?q=multimodal+out-of-distribution+detection&type=repositories`
- `paper`: `https://arxiv.org/search/?query=recent+agent+hallucination+paper&searchtype=all&source=header`
- `shopping`: `https://cn.bing.com/search?q=best+headphones+2024+comparison+review+review+price`

## 结论

- 三个场景均可正常输入并产出结构化输出（`ok=true`，步骤通过）。
- `github` 与 `paper` 报告字段完整。
- `shopping` 场景存在 `report.recommendations` 缺失（其余流程正常）。

## 关键产物路径

- `runs/latest-run-github-llm.json`
- `runs/latest-run-paper-llm.json`
- `runs/latest-run-shopping-llm.json`
- `runs/screenshots/`（运行截图证据）
