from __future__ import annotations

import re
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

REQUIREMENT_SLOT_HINTS = {
    "form_fields": "form page fields required hints",
    "form_validation": "validation errors submit confirmation",
    "approval_gate": "safe draft fill review",
    "booking_inventory": "available slots rooms tickets price",
    "booking_constraints": "filters price time cancellation policy",
    "lead_candidates": "companies contacts emails titles",
    "lead_fields": "structured fields email title location",
    "lead_verification": "source page verification",
    "baseline_state": "current price stock status",
    "alert_conditions": "threshold change alert condition",
    "monitor_follow_up": "follow-up page checks",
    "qa_checkpoints": "critical path ui elements",
    "qa_assertions": "expected success error states",
    "qa_bug_evidence": "bug evidence screenshot reproduction",
    "video_candidates": "video tutorial explanation",
    "transcript_notes": "transcript notes key points",
    "visual_evidence": "demo slides screen recording",
    "comments_discussion": "video comments discussion questions",
    "candidate_pool": "best comparison review price",
    "marketplace_pages": "official product page price specs reviews",
    "comparative_reviews": "expert review comparison drawbacks",
    "user_comments": "user reviews complaints pros cons",
    "video_reviews": "video review comments",
    "repo_candidates": "repository candidates",
    "repo_metadata": "stars forks license updated",
    "implementation_docs": "readme examples docs",
    "ecosystem_comparison": "alternatives benchmark comparison",
    "seed_papers": "arxiv paper",
    "related_work": "survey benchmark related work",
    "reproducibility": "code dataset github",
    "limitations": "limitations failure cases evaluation",
    "orientation": "overview",
    "primary_sources": "official documentation primary source",
    "cross_validation": "comparison alternatives limitations",
}

# Legacy alias kept while the strategy layer migrates from query-first naming
# to evidence-plan naming.
REQUIREMENT_SLOT_QUERIES = REQUIREMENT_SLOT_HINTS


def github_reference_notes() -> List[Dict[str, str]]:
    return REFERENCE_REPOS


def github_search_query(goal: str) -> str:
    text = str(goal or "").strip().lower()
    if not text:
        return "browser automation agent"
    if ("浏览器" in goal or "browser" in text) and ("自动化" in goal or "automation" in text) and ("智能体" in goal or "agent" in text):
        return "browser automation agent 智能体"
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fa5\s]+", " ", text)
    for phrase in [
        "帮我找几个可以参考的",
        "可以参考的",
        "适合借鉴的实现点",
        "比较活跃度",
        "开源项目",
        "实现点",
        "质量",
    ]:
        normalized = normalized.replace(phrase, " ")
    tokens = [token for token in normalized.split() if token]
    stopwords = {
        "帮我",
        "找",
        "几个",
        "可以",
        "参考",
        "比较",
        "活跃度",
        "语言",
        "质量",
        "适合",
        "借鉴",
        "实现点",
        "开源",
        "项目",
        "仓库",
        "github",
        "repo",
        "repository",
        "the",
        "and",
        "for",
        "with",
        "that",
        "浏览器自动化智能体",
        "比较活跃度",
        "适合借鉴的实现点",
        "开源项目",
        "readme质量和适合借鉴的实现点",
    }
    kept: List[str] = []
    for token in tokens:
        if token in stopwords:
            continue
        if any(ch.isdigit() for ch in token) and len(token) <= 2:
            continue
        kept.append(token)
    priorities = [
        "browser",
        "automation",
        "agent",
        "llm",
        "playwright",
        "crawler",
        "scraper",
        "research",
        "多模态",
        "浏览器",
        "自动化",
        "智能体",
    ]
    ordered: List[str] = []
    for token in priorities:
        if token in kept and token not in ordered:
            ordered.append(token)
    for token in kept:
        if token not in ordered:
            ordered.append(token)
    if not ordered:
        return "browser automation agent"
    return " ".join(ordered[:6])


def requirement_slots(domain: str, goal: str) -> List[Dict[str, str]]:
    text = goal.lower()
    if domain == "form":
        return [
            {"slot": "form_fields", "purpose": "识别表单字段、必填项和占位提示", "source": "general"},
            {"slot": "form_validation", "purpose": "识别校验提示、成功提示和提交风险", "source": "general"},
            {"slot": "approval_gate", "purpose": "确保只做草稿填写并在提交前停下", "source": "general"},
        ]
    if domain == "booking":
        return [
            {"slot": "booking_inventory", "purpose": "建立可预订资源候选池", "source": "general"},
            {"slot": "booking_constraints", "purpose": "核对时间、价格和规则限制", "source": "general"},
            {"slot": "approval_gate", "purpose": "进入确认页但不提交", "source": "general"},
        ]
    if domain == "lead":
        return [
            {"slot": "lead_candidates", "purpose": "建立线索候选池", "source": "general"},
            {"slot": "lead_fields", "purpose": "补齐结构化字段", "source": "general"},
            {"slot": "lead_verification", "purpose": "保留来源和可追溯证据", "source": "general"},
        ]
    if domain == "monitoring":
        return [
            {"slot": "baseline_state", "purpose": "抓取当前基线状态", "source": "general"},
            {"slot": "alert_conditions", "purpose": "明确继续监视的触发条件", "source": "general"},
            {"slot": "monitor_follow_up", "purpose": "设计后续继续观察和补动作的线索", "source": "general"},
        ]
    if domain == "qa":
        return [
            {"slot": "qa_checkpoints", "purpose": "识别关键页面元素和主流程", "source": "general"},
            {"slot": "qa_assertions", "purpose": "明确通过/失败判据", "source": "general"},
            {"slot": "qa_bug_evidence", "purpose": "准备失败定位和复现证据", "source": "general"},
        ]
    if domain == "video":
        return [
            {"slot": "video_candidates", "purpose": "寻找主题相关视频候选和讲解来源", "source": "video"},
            {"slot": "transcript_notes", "purpose": "寻找字幕、章节、笔记或文字整理", "source": "general"},
            {"slot": "visual_evidence", "purpose": "寻找包含演示、屏幕或幻灯片的视觉证据", "source": "video"},
            {"slot": "comments_discussion", "purpose": "观察评论区、讨论和常见疑问", "source": "video"},
        ]
    if domain == "shopping":
        return [
            {"slot": "candidate_pool", "purpose": "建立候选池和价格范围", "source": "shopping"},
            {"slot": "marketplace_pages", "purpose": "进入商城/商品页线索，核对参数、价格和评价入口", "source": "shopping"},
            {"slot": "comparative_reviews", "purpose": "收集专业评测和横向对比", "source": "general"},
            {"slot": "user_comments", "purpose": "收集用户评论、差评和常见问题", "source": "shopping"},
            {"slot": "video_reviews", "purpose": "观察视频测评和评论区线索", "source": "video"},
        ]
    if domain == "github":
        return [
            {"slot": "repo_candidates", "purpose": "发现候选仓库和同类项目", "source": "github"},
            {"slot": "repo_metadata", "purpose": "收集活跃度、许可证和维护质量信号", "source": "github"},
            {"slot": "implementation_docs", "purpose": "检查 README、安装说明、示例和可运行性", "source": "github"},
            {"slot": "ecosystem_comparison", "purpose": "寻找竞品、基准和横向比较线索", "source": "general"},
        ]
    if domain == "paper":
        return [
            {"slot": "seed_papers", "purpose": "发现种子论文和核心方法", "source": "paper"},
            {"slot": "related_work", "purpose": "扩展综述、基准和相关工作脉络", "source": "paper"},
            {"slot": "reproducibility", "purpose": "检查代码、数据集和复现资源", "source": "github"},
            {"slot": "limitations", "purpose": "收集局限性、评测指标和失败案例", "source": "general"},
        ]
    if "浏览器" in goal or "browser" in text:
        if "github" in text or "仓库" in goal or "开源" in goal:
            return [
                {"slot": "repo_candidates", "purpose": "发现候选仓库和同类项目", "source": "github"},
                {"slot": "repo_metadata", "purpose": "收集活跃度、许可证和维护质量信号", "source": "github"},
                {"slot": "implementation_docs", "purpose": "检查 README、安装说明、示例和可运行性", "source": "github"},
            ]
        return [
            {"slot": "orientation", "purpose": "建立任务背景和关键实体", "source": "general"},
            {"slot": "primary_sources", "purpose": "寻找官方文档、原始资料或一手来源", "source": "general"},
            {"slot": "cross_validation", "purpose": "交叉验证替代方案、争议和限制", "source": "general"},
        ]
    return [
        {"slot": "orientation", "purpose": "建立任务背景和关键实体", "source": "general"},
        {"slot": "primary_sources", "purpose": "寻找官方文档、原始资料或一手来源", "source": "general"},
        {"slot": "cross_validation", "purpose": "交叉验证替代方案、争议和限制", "source": "general"},
    ]


def default_decision_criteria(domain: str, goal: str) -> List[Dict[str, str]]:
    text = goal.lower()
    if domain == "form":
        return [
            {"name": "字段识别", "why_it_matters": "先确认页面上有哪些真实可填写字段", "evidence_to_collect": "表单项、必填项、占位符、校验提示"},
            {"name": "填写安全", "why_it_matters": "避免提交账号、密码或敏感数据", "evidence_to_collect": "敏感字段、提交按钮、审批点"},
            {"name": "完成验证", "why_it_matters": "填写后要确认页面状态是否满足目标", "evidence_to_collect": "错误提示、成功提示、字段回显"},
        ]
    if domain == "booking":
        return [
            {"name": "资源候选", "why_it_matters": "预订前要先找到可选资源", "evidence_to_collect": "房型、时间段、票档、库存"},
            {"name": "限制条件", "why_it_matters": "价格、时间和规则直接决定是否可行", "evidence_to_collect": "价格、时间、取消规则、人数限制"},
            {"name": "人工审批", "why_it_matters": "真正提交前必须停在人审点", "evidence_to_collect": "确认页、提交按钮、订单摘要"},
        ]
    if domain == "lead":
        return [
            {"name": "目标匹配", "why_it_matters": "线索需要符合行业和目标条件", "evidence_to_collect": "公司、职位、地区、业务标签"},
            {"name": "结构化字段", "why_it_matters": "后续导出和使用依赖字段质量", "evidence_to_collect": "姓名、邮箱、职位、来源页"},
            {"name": "可追溯性", "why_it_matters": "线索要能回到来源核查", "evidence_to_collect": "来源链接、摘录、页面快照"},
        ]
    if domain == "monitoring":
        return [
            {"name": "目标状态", "why_it_matters": "监控需要明确当前页面是否达标", "evidence_to_collect": "价格、库存、状态文本、更新时间"},
            {"name": "变化线索", "why_it_matters": "要知道什么变化值得继续动作", "evidence_to_collect": "阈值、变更项、警报条件"},
            {"name": "持续观察", "why_it_matters": "不是一次检查，而是循环确认", "evidence_to_collect": "监视轨迹、后续页面动作、最终状态"},
        ]
    if domain == "qa":
        return [
            {"name": "关键路径", "why_it_matters": "回归测试要覆盖真正影响使用的主流程", "evidence_to_collect": "按钮、输入框、跳转、错误提示"},
            {"name": "断言证据", "why_it_matters": "需要明确什么算通过或失败", "evidence_to_collect": "可见 UI 状态、页面文本、结果页"},
            {"name": "失败定位", "why_it_matters": "发现问题后要能快速复现", "evidence_to_collect": "步骤轨迹、截图、失败页面"},
        ]
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


def default_evidence_plan(domain: str, goal: str) -> List[Dict[str, str]]:
    plan: List[Dict[str, str]] = []
    effective_domain = domain
    lowered_goal = goal.lower()
    if domain == "general" and (
        "github" in lowered_goal
        or "仓库" in goal
        or "开源" in goal
        or "repo" in lowered_goal
        or "repository" in lowered_goal
    ):
        effective_domain = "github"
    base_intent = github_search_query(goal) if effective_domain == "github" else goal
    for item in requirement_slots(effective_domain, goal):
        slot = str(item.get("slot") or "")
        slot_hint = REQUIREMENT_SLOT_HINTS.get(slot, slot.replace("_", " "))
        plan.append(
            {
                "query": f"{base_intent} {slot_hint}".strip(),
                "purpose": str(item.get("purpose") or slot),
                "source": str(item.get("source") or "general"),
                "evidence_stage": slot,
                "requirement_slot": slot,
            }
        )
    return plan


def default_search_plan(domain: str, goal: str) -> List[Dict[str, str]]:
    return default_evidence_plan(domain, goal)
