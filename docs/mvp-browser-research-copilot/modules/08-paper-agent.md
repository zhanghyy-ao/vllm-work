# 模块文档：Paper Agent

## 职责
执行“论文研究”任务：检索近期论文、抽取核心信息、对比并总结。

## 输入
- 研究问题（如：Agent hallucination）
- 时间范围、会议偏好

## 输出
- 论文列表
- 方法/数据集/指标对比
- related work 草稿材料

## 子流程
1. Retrieval：arXiv / Scholar / 代码仓库交叉检索
2. Parsing：摘要 + 关键段落抽取
3. Structuring：方法、设置、结果、局限统一字段
4. Validation：引用与结论一致性检查
5. Summarization：结构化综述输出

## 关键接口
- `run_paper_research(request) -> StructuredReport`
- `extract_paper_fields(source_doc) -> PaperCard`

## 特有恢复策略
- 命中不足：扩展同义词/相关术语
- 信息冲突：标记不确定并追加来源

## 测试要点
- 同一论文多源抽取字段一致
- 结论带来源引用
- 近两年过滤准确
