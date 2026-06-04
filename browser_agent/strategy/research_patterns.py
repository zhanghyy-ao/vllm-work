from __future__ import annotations

from typing import Any, Dict, List


REFERENCE_REPOS = [
    {
        "name": "browser-use/browser-use",
        "url": "https://github.com/browser-use/browser-use",
        "pattern": "browser-state driven automation with an LLM controller and reusable browser tools",
    },
    {
        "name": "mendableai/firecrawl",
        "url": "https://github.com/mendableai/firecrawl",
        "pattern": "search/crawl/scrape pipeline that converts web pages into clean structured content",
    },
    {
        "name": "TencentCloudADP/youtu-agent",
        "url": "https://github.com/TencentCloudADP/youtu-agent",
        "pattern": "multi-agent decomposition and tool execution for broad browser/research tasks",
    },
    {
        "name": "Gemini API multimodal examples",
        "url": "https://github.com/google-gemini/generative-ai-python",
        "pattern": "Gemini-powered image/video understanding interface for future multimodal page/video analysis",
    },
]


def github_reference_notes() -> List[Dict[str, str]]:
    return REFERENCE_REPOS


def default_decision_criteria(domain: str, goal: str) -> List[Dict[str, str]]:
    text = goal.lower()
    if domain == "shopping":
        return [
            {"name": "预算/价格", "why_it_matters": "推荐必须满足用户预算并比较性价比", "evidence_to_collect": "价格区间、促销、保修与平台来源"},
            {"name": "品牌与型号", "why_it_matters": "品牌决定售后、稳定性和生态兼容", "evidence_to_collect": "候选品牌、型号、发布日期与口碑"},
            {"name": "类型/场景适配", "why_it_matters": "通勤、办公、运动等场景对形态要求不同", "evidence_to_collect": "入耳/头戴/开放式、重量、便携性"},
            {"name": "核心体验", "why_it_matters": "音质、降噪、舒适度影响长期使用", "evidence_to_collect": "专业评测和用户评论里的优缺点"},
            {"name": "风险点", "why_it_matters": "推荐需要说明缺陷而不是只给优点", "evidence_to_collect": "差评、常见故障、连接稳定性和佩戴疲劳"},
        ]
    if domain == "video":
        return [
            {"name": "主题匹配", "why_it_matters": "先判断视频是否真正覆盖用户问题", "evidence_to_collect": "标题、简介、章节、字幕关键词"},
            {"name": "信息完整度", "why_it_matters": "整理内容需要覆盖背景、步骤和结论", "evidence_to_collect": "字幕、页面文本、评论摘要、关键时间点"},
            {"name": "可引用证据", "why_it_matters": "输出需要能回到视频来源", "evidence_to_collect": "视频 URL、作者、发布时间、章节或片段"},
            {"name": "视觉信息", "why_it_matters": "教程/演示类视频常有屏幕和图像信息", "evidence_to_collect": "截图、关键帧和后续 Gemini 视觉识别结果"},
        ]
    if domain == "github":
        return [
            {"name": "活跃度", "why_it_matters": "活跃项目更适合复用", "evidence_to_collect": "stars、forks、最近提交、issue 状态"},
            {"name": "可运行性", "why_it_matters": "浏览器工作需要能落地执行", "evidence_to_collect": "README、安装说明、示例代码、许可证"},
            {"name": "任务匹配", "why_it_matters": "避免只按关键词命中", "evidence_to_collect": "功能说明、工具接口和示例任务"},
        ]
    if domain == "paper":
        return [
            {"name": "方法相关性", "why_it_matters": "论文需要服务当前实现", "evidence_to_collect": "方法、任务设定和实验对象"},
            {"name": "可复现性", "why_it_matters": "优先选择有代码/数据的工作", "evidence_to_collect": "代码链接、数据集、实验设置"},
            {"name": "新近性", "why_it_matters": "Agent 和多模态进展很快", "evidence_to_collect": "年份、版本和引用上下文"},
        ]
    if "浏览器" in goal or "browser" in text:
        return [
            {"name": "页面状态", "why_it_matters": "浏览器助理必须根据当前页面继续行动", "evidence_to_collect": "URL、标题、正文、可点击元素"},
            {"name": "任务完成度", "why_it_matters": "需要判断是否满足用户目标", "evidence_to_collect": "目标关键词、结果页、错误/空结果信号"},
        ]
    return [
        {"name": "相关性", "why_it_matters": "确保资料直接回答目标", "evidence_to_collect": "标题、摘要、正文证据"},
        {"name": "可信度", "why_it_matters": "减少低质量来源影响", "evidence_to_collect": "来源、作者、发布时间和交叉验证"},
        {"name": "可行动性", "why_it_matters": "输出应能指导下一步", "evidence_to_collect": "步骤、链接、推荐和风险"},
    ]


def default_search_plan(domain: str, goal: str) -> List[Dict[str, str]]:
    if domain == "video":
        return [
            {"query": f"{goal} video tutorial explanation", "purpose": "寻找主题相关视频候选和讲解来源", "source": "video", "evidence_stage": "video_candidates"},
            {"query": f"{goal} transcript notes key points", "purpose": "寻找字幕、章节、笔记或文字整理", "source": "general", "evidence_stage": "transcript_notes"},
            {"query": f"{goal} demo slides screen recording", "purpose": "寻找包含演示、屏幕或幻灯片的视觉证据", "source": "video", "evidence_stage": "visual_evidence"},
            {"query": f"{goal} video comments discussion questions", "purpose": "观察评论区、讨论和常见疑问", "source": "video", "evidence_stage": "comments_discussion"},
        ]
    if domain == "shopping":
        if "耳机" in goal:
            budget = "1000元以内" if "1000" in goal else "预算内"
            return [
                {
                    "query": f"site:post.smzdm.com {budget} 头戴式 降噪耳机 推荐 评测 通勤 办公",
                    "purpose": "建立预算内主流品牌/型号候选池和初步价格范围",
                    "source": "shopping",
                    "evidence_stage": "candidate_pool",
                },
                {
                    "query": f"{budget} 降噪耳机 京东 天猫 官方 商品页 参数 价格 用户评价",
                    "purpose": "进入商城/商品页线索，核对价格、参数、销量和评价入口",
                    "source": "shopping",
                    "evidence_stage": "marketplace_pages",
                },
                {
                    "query": "WH-CH720N W820NB Space Q45 降噪耳机 对比 评测 缺点",
                    "purpose": "围绕具体型号比较音质、降噪、舒适度和短板",
                    "source": "shopping",
                    "evidence_stage": "comparative_reviews",
                },
                {
                    "query": "WH-CH720N W820NB Space Q45 京东 天猫 用户评价 差评 佩戴 舒适度 底噪 夹头",
                    "purpose": "收集用户评论、差评、佩戴疲劳和常见故障",
                    "source": "general",
                    "evidence_stage": "user_comments",
                },
                {
                    "query": "WH-CH720N W820NB Space Q45 降噪耳机 测评 视频 B站 YouTube 用户评论",
                    "purpose": "观察专业视频测评、可见字幕/简介和评论区线索",
                    "source": "video",
                    "evidence_stage": "video_reviews",
                },
            ]
        return [
            {"query": f"{goal} best comparison review price", "purpose": "建立候选池和价格范围", "source": "shopping", "evidence_stage": "candidate_pool"},
            {"query": f"{goal} official product page price specs reviews", "purpose": "进入商城/商品页线索，核对参数、价格和评价入口", "source": "shopping", "evidence_stage": "marketplace_pages"},
            {"query": f"{goal} expert review comparison drawbacks", "purpose": "收集专业评测和横向对比", "source": "general", "evidence_stage": "comparative_reviews"},
            {"query": f"{goal} user reviews complaints pros cons", "purpose": "收集用户评论、差评和常见问题", "source": "shopping", "evidence_stage": "user_comments"},
            {"query": f"{goal} video review comments", "purpose": "观察视频测评和评论区线索", "source": "video", "evidence_stage": "video_reviews"},
        ]
    if domain == "github":
        return [
            {"query": f"{goal} GitHub repository", "purpose": "发现候选仓库和同类项目", "source": "github", "evidence_stage": "repo_candidates"},
            {"query": f"{goal} stars forks license recently updated GitHub", "purpose": "收集活跃度、许可证和维护质量信号", "source": "github", "evidence_stage": "repo_metadata"},
            {"query": f"{goal} README installation examples documentation", "purpose": "检查 README、安装说明、示例和可运行性", "source": "github", "evidence_stage": "implementation_docs"},
            {"query": f"{goal} alternatives comparison benchmark", "purpose": "寻找竞品、基准和横向比较线索", "source": "general", "evidence_stage": "ecosystem_comparison"},
        ]
    if domain == "paper":
        return [
            {"query": f"{goal} arxiv paper", "purpose": "发现种子论文和核心方法", "source": "paper", "evidence_stage": "seed_papers"},
            {"query": f"{goal} survey benchmark related work", "purpose": "扩展综述、基准和相关工作脉络", "source": "paper", "evidence_stage": "related_work"},
            {"query": f"{goal} code dataset github", "purpose": "检查代码、数据集和复现资源", "source": "github", "evidence_stage": "reproducibility"},
            {"query": f"{goal} limitations failure cases evaluation", "purpose": "收集局限性、评测指标和失败案例", "source": "general", "evidence_stage": "limitations"},
        ]
    return [
        {"query": f"{goal} overview", "purpose": "建立任务背景和关键实体", "source": "general", "evidence_stage": "orientation"},
        {"query": f"{goal} official documentation primary source", "purpose": "寻找官方文档、原始资料或一手来源", "source": "general", "evidence_stage": "primary_sources"},
        {"query": f"{goal} comparison alternatives limitations", "purpose": "交叉验证替代方案、争议和限制", "source": "general", "evidence_stage": "cross_validation"},
    ]
