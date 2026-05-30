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
            {"query": f"{goal} video tutorial summary", "purpose": "寻找主题相关视频和讲解资料", "source": "video"},
            {"query": f"{goal} transcript notes key points", "purpose": "寻找字幕、笔记或文字整理", "source": "general"},
            {"query": f"{goal} demo explanation", "purpose": "寻找演示类内容以便后续视觉识别", "source": "video"},
        ]
    if domain == "shopping":
        if "耳机" in goal:
            budget = "1000元以内" if "1000" in goal else "预算内"
            return [
                {
                    "query": f"site:post.smzdm.com {budget} 头戴式 降噪耳机 推荐 评测 通勤 办公",
                    "purpose": "收集预算内主流品牌/型号候选和价格范围",
                    "source": "shopping",
                },
                {
                    "query": "WH-CH720N W820NB Space Q45 降噪耳机 对比 评测 缺点",
                    "purpose": "围绕具体型号比较音质、降噪、舒适度和短板",
                    "source": "shopping",
                },
                {
                    "query": f"{budget} 降噪耳机 用户评价 佩戴舒适度 差评",
                    "purpose": "收集用户评价、佩戴疲劳和常见问题",
                    "source": "general",
                },
            ]
        return [
            {"query": f"{goal} best comparison review price", "purpose": "收集候选清单和价格范围", "source": "shopping"},
            {"query": f"{goal} user reviews pros cons", "purpose": "收集用户评价和常见问题", "source": "shopping"},
            {"query": f"{goal} expert review comparison", "purpose": "收集专业评测对比", "source": "general"},
        ]
    return [{"query": goal, "purpose": "围绕用户目标收集基础资料", "source": domain if domain != "auto" else "general"}]
