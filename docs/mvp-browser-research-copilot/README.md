# Browser Research Copilot - MVP 文档总览

## 文档目标
这套文档用于指导 Browser Research Copilot 的第一版落地，覆盖：
- 系统模块图与接口
- MVP 仓库结构
- 功能模块职责与 I/O 协议
- 快速开发顺序

## 文档目录
- [01-system-module-diagram-and-interfaces.md](./01-system-module-diagram-and-interfaces.md)
- [02-mvp-repository-structure.md](./02-mvp-repository-structure.md)
- [03-feature-spec.md](./03-feature-spec.md)
- [04-code-walkthrough.md](./04-code-walkthrough.md)
- [modules/01-planner.md](./modules/01-planner.md)
- [modules/02-browser-harness.md](./modules/02-browser-harness.md)
- [modules/03-page-understanding.md](./modules/03-page-understanding.md)
- [modules/04-memory.md](./modules/04-memory.md)
- [modules/05-verifier.md](./modules/05-verifier.md)
- [modules/06-output-and-report.md](./modules/06-output-and-report.md)
- [modules/07-github-agent.md](./modules/07-github-agent.md)
- [modules/08-paper-agent.md](./modules/08-paper-agent.md)

## MVP 推荐范围
第一阶段只做两个垂直任务：
1. GitHub 开源项目研究
2. 论文检索与对比总结

原因：
- 数据结构更稳定（Repo / Paper 元数据）
- 指标可定义（命中率、证据充分性、结论一致性）
- 与 Harness 重试策略耦合紧，容易做出差异化
