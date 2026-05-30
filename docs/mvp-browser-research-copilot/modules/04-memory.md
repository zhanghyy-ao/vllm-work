# 模块文档：Memory

## 职责
管理会话级上下文、用户偏好与证据索引，支持跨步骤检索。

## 输入
- `EvidenceItem`
- `UserProfile`
- Run Context

## 输出
- 检索结果（top-k evidence）
- 偏好注入（constraints patch）

## 关键接口
- `save_evidence(item: EvidenceItem) -> None`
- `query_evidence(query: str, top_k: int) -> list[EvidenceItem]`
- `load_profile(user_id: str) -> UserProfile`

## 数据分层
- Session Memory：当前任务临时数据
- Profile Memory：长期偏好
- Evidence Index：可检索证据片段

## 测试要点
- 相同 query 的检索稳定
- profile 更新不影响历史 run 可追溯性
