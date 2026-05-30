# 模块文档：GitHub Agent

## 职责
执行“开源项目研究”任务：搜索、筛选、阅读、比较、推荐。

## 输入
- 目标主题（如：multimodal OOD）
- 约束（star、活跃度、许可证、语言）

## 输出
- Repo 候选列表
- 技术路线摘要
- 推荐 Top-N

## 子流程
1. Search：GitHub 搜索 + 关键词扩展
2. Inspect：读取 README、Issue、最近提交
3. Extract：提取 star/fork/update/license/tasks
4. Compare：按评分策略排序
5. Report：输出推荐与证据

## 关键接口
- `run_github_research(request) -> StructuredReport`
- `score_repo(repo_features) -> float`

## 特有恢复策略
- 低质量结果：自动改写关键词重新搜
- README 缺失：切换看论文链接/仓库文档

## 测试要点
- 多关键词回退能提升有效候选数
- 同主题重复运行结果波动可控
