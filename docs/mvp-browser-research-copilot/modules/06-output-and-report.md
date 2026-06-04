# 模块文档：Output & Report

## 职责
将证据集合构造成结构化报告，产出推荐与对比。

## 输入
- `EvidenceItem[]`
- `RunMetadata`

## 输出
- `StructuredReport`
- Markdown/JSON 两种格式

## 关键接口
- `build_report(evidence_bundle) -> StructuredReport`
- `render_markdown(report) -> str`

## 输出模板
- 摘要
- 候选列表
- 对比表（指标/优缺点）
- 推荐结论
- 不确定性说明
- 下一步行动

## 测试要点
- 报告中的每条结论可追溯到 evidence
- 缺字段时给出不确定性声明
