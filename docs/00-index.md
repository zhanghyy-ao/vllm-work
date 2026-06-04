# Harness 文档索引

当前 `docs/` 只保留三类内容：

- 总览索引
- 与其他工作的对比
- 对当前 Harness 架构和代码实现的系统讲解

删除的内容主要是测试报告、验收记录、重复的方案稿，以及把同一件事拆得过碎的多份文档。这样做的目的很简单：让读者进入 `docs/` 之后，看到的是一条清晰主线，而不是一堆背景材料。

## 建议阅读顺序

1. [market-comparison.md](./market-comparison.md)
   先回答“这个项目和 OpenAI Operator、Anthropic Computer Use、Browser Use、Project Mariner 这类工作相比，差异到底在哪里”。

2. [harness-architecture.md](./harness-architecture.md)
   这是主文档，集中讲当前仓库里的 Harness 架构、两条运行路径、核心数据结构、模块边界和运行时协作方式。

3. [harness-code-walkthrough.md](./harness-code-walkthrough.md)
   从 `app.py` 开始，顺着真实代码把一次运行走通，适合边看文档边打开代码。

## 当前文档集的目标

这套文档不再追求“把所有想法都留档”，而是只回答三个工程上最重要的问题：

- 这个项目和其他浏览器智能体工作相比，定位是什么
- 当前仓库里的 Harness 到底是怎么组织起来的
- 如果要读代码或继续开发，应该从哪里进入
