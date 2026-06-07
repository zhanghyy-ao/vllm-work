from __future__ import annotations

import re
from typing import List


QUERY_STAGE_PRIORITIES = {
    "github": ["browser", "automation", "agent", "智能体", "浏览器", "自动化", "web", "assistant"],
    "shopping": ["降噪耳机", "耳机", "headphone", "anc", "降噪", "1000元以内", "通勤", "办公室"],
    "video": ["tutorial", "视频", "教程", "course", "clip", "multimodal", "多模态"],
    "paper": ["paper", "benchmark", "agent", "browser", "论文", "基准"],
    "comparative_reviews": ["降噪耳机", "耳机", "review", "评测", "compare", "对比"],
    "user_comments": ["降噪耳机", "耳机", "comment", "评论", "差评", "complaint"],
    "repo_metadata": ["browser", "automation", "agent", "github", "repository"],
    "implementation_docs": ["browser", "automation", "agent", "readme", "install", "example"],
}


def requirement_driven_query(goal: str, domain: str, target_stage: str) -> str:
    goal_text = str(goal or "").strip()
    if not goal_text:
        return ""
    slot_suffix = {
        "repo_candidates": "github repository",
        "repo_metadata": "stars forks license",
        "implementation_docs": "readme install example",
        "ecosystem_comparison": "alternatives benchmark",
        "candidate_pool": "推荐 对比",
        "marketplace_pages": "商品 参数 价格",
        "comparative_reviews": "评测 对比",
        "user_comments": "用户 差评",
        "video_reviews": "视频 评测",
        "video_candidates": "video tutorial",
        "transcript_notes": "transcript chapter",
        "visual_evidence": "demo screen",
        "orientation": "overview",
        "primary_sources": "official documentation",
        "cross_validation": "comparison limitations",
    }
    core = minimal_query_core(goal_text, domain, target_stage)
    suffix = slot_suffix.get(target_stage, "")
    parts = [part for part in [core, suffix] if part]
    return " ".join(parts).strip()


def minimal_query_core(goal_text: str, domain: str, target_stage: str) -> str:
    stage_priority_terms = QUERY_STAGE_PRIORITIES.get(target_stage, [])
    domain_priority_terms = QUERY_STAGE_PRIORITIES.get(domain, [])
    extracted = extract_priority_terms(goal_text, [*stage_priority_terms, *domain_priority_terms], max_terms=4 if domain == "github" else 6)
    if extracted:
        return extracted
    if domain == "github" or target_stage.startswith("repo_"):
        return compact_goal_terms(goal_text, max_terms=4)
    if domain == "shopping":
        product_terms = compact_goal_terms(goal_text, max_terms=6)
        return product_terms or goal_text[:40]
    if domain == "video":
        return compact_goal_terms(goal_text, max_terms=5)
    return compact_goal_terms(goal_text, max_terms=5)


def extract_priority_terms(goal_text: str, priorities: List[str], max_terms: int) -> str:
    normalized = str(goal_text or "").lower()
    if "1000元以内" in goal_text and "降噪耳机" in goal_text:
        merged = ["1000元以内降噪耳机"]
        for term in priorities:
            if term in {"1000元以内", "降噪耳机", "耳机", "降噪"}:
                continue
            if term.lower() in normalized and term not in merged:
                merged.append(term)
        return " ".join(merged[:max_terms])
    picked: List[str] = []
    for term in priorities:
        if term.lower() in normalized and term not in picked:
            picked.append(term)
    merged: List[str] = []
    skip_terms = set()
    for term in picked:
        if term in skip_terms:
            continue
        combined = None
        for other in picked:
            if term == other or other in skip_terms:
                continue
            if term in other:
                skip_terms.add(term)
                combined = other
                break
        merged.append(combined or term)
    deduped: List[str] = []
    for term in merged:
        if term not in deduped:
            deduped.append(term)
    return " ".join(deduped[:max_terms])


def compact_goal_terms(goal_text: str, max_terms: int = 5) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fa5\s]+", " ", goal_text)
    for prefix in ["推荐", "调研", "整理", "查找", "帮我"]:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
    raw_terms = [term for term in normalized.split() if term]
    stopwords = {
        "帮我",
        "找",
        "几个",
        "可以",
        "参考",
        "比较",
        "推荐",
        "一款",
        "适合",
        "查找",
        "调研",
        "整理",
        "近期",
        "相关",
        "产品",
        "项目",
        "仓库",
        "开源",
        "实现",
        "实现点",
        "质量",
        "活跃度",
        "语言",
        "和",
        "的",
    }
    kept: List[str] = []
    for term in raw_terms:
        if term.lower() in stopwords or term in stopwords:
            continue
        if len(term) == 1 and not term.isdigit():
            continue
        kept.append(term)
    return " ".join(kept[:max_terms])
