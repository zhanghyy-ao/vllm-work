# 模块文档：Verifier

## 职责
对每步结果做质量与一致性校验，决定通过或重试。

## 输入
- `StepResult`
- `Observation`
- `SuccessCriteria`

## 输出
- `VerificationResult`

## 关键接口
- `verify(step_result, criteria) -> VerificationResult`
- `score_evidence(evidence_items) -> float`

## 检查项
- Schema 完整性：必填字段齐全
- Evidence 充分性：结论有来源支持
- 一致性：页面内容与提取字段不冲突

## 失败策略
- 返回 `retry_hint`（关键词改写、补抽字段、换来源）

## 测试要点
- 错误字段能被识别
- 空证据结论必须 fail
- 低置信度自动触发 retry
