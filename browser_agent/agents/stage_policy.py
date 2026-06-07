from __future__ import annotations

from typing import Any, Dict, List

from browser_agent.types import Observation


STAGE_TEXT_CUES = {
    "comparative_reviews": ["review", "compare", "评测", "对比"],
    "marketplace_pages": ["product", "商品", "参数", "京东", "天猫", "官方"],
    "repo_candidates": ["github", "repository", "repo", "search"],
    "repo_metadata": ["stars", "forks", "license", "updated"],
    "implementation_docs": ["readme", "installation", "example", "documentation"],
    "video_candidates": ["video", "bilibili", "youtube", "watch", "视频"],
    "transcript_notes": ["transcript", "chapter", "字幕", "章节", "notes", "笔记"],
    "user_comments": ["comment", "评论", "complaint", "差评", "故障"],
    "video_reviews": ["video", "youtube", "bilibili", "视频", "字幕", "评论区"],
    "ecosystem_comparison": ["alternative", "benchmark", "comparison", "竞品"],
    "seed_papers": ["paper", "arxiv", "论文"],
    "related_work": ["survey", "related", "benchmark", "综述"],
    "reproducibility": ["code", "dataset", "github", "复现"],
    "limitations": ["limitation", "failure", "局限", "失败"],
    "visual_evidence": ["slide", "screen", "visual", "演示", "关键帧"],
    "comments_discussion": ["comment", "discussion", "评论", "讨论"],
    "orientation": ["overview", "background", "概览", "背景"],
    "primary_sources": ["official", "documentation", "官方"],
    "cross_validation": ["compare", "alternative", "limitations", "对比"],
}

DETAIL_STAGES = {
    "comparative_reviews",
    "user_comments",
    "repo_metadata",
    "implementation_docs",
    "ecosystem_comparison",
    "transcript_notes",
    "visual_evidence",
}

CANDIDATE_STAGES = {"candidate_pool", "repo_candidates", "video_candidates", "seed_papers"}
LINK_SIGNAL_STAGES = {"candidate_pool", "repo_candidates", "video_candidates"}
DEEP_READ_SIGNAL_STAGES = {
    "repo_metadata",
    "implementation_docs",
    "comparative_reviews",
    "ecosystem_comparison",
    "marketplace_pages",
    "user_comments",
}

SIGNAL_FIELD_MAP = {
    "candidate_pool": "candidate_pool_signals",
    "repo_candidates": "repo_candidate_signals",
    "video_candidates": "video_candidate_signals",
    "repo_metadata": "repo_metadata_signals",
    "implementation_docs": "implementation_doc_signals",
    "comparative_reviews": "review_signals",
    "ecosystem_comparison": "comparison_signals",
    "marketplace_pages": "marketplace_signals",
    "user_comments": "comment_signals",
    "transcript_notes": "transcript_signals",
    "visual_evidence": "visual_signals",
}


def slot_signal_present_in_fields(stage: str, fields: Dict[str, Any]) -> bool:
    if fields.get("requirement_slot") == stage or fields.get("evidence_stage") == stage:
        signal_key = SIGNAL_FIELD_MAP.get(stage, "requirement_slot_signals")
        payload = fields.get(signal_key)
        if isinstance(payload, dict) and payload:
            return True
        if stage in LINK_SIGNAL_STAGES and isinstance(fields.get("links"), list) and fields.get("links"):
            return True
        if stage in DEEP_READ_SIGNAL_STAGES and isinstance(fields.get("deep_reads"), list) and fields.get("deep_reads"):
            return True
        if stage == "transcript_notes" and isinstance(fields.get("video_digest"), dict):
            return True
    return False


def slot_signal_present_from_action(stage: str, action: Any, fields: Dict[str, Any]) -> bool:
    action_name = str(action or "")
    if stage in LINK_SIGNAL_STAGES and action_name == "collect_links":
        return isinstance(fields.get("links"), list) and bool(fields.get("links"))
    if stage in DEEP_READ_SIGNAL_STAGES and action_name == "deep_read_candidates":
        return True
    if stage == "transcript_notes" and action_name == "extract_video":
        return isinstance(fields.get("video_digest"), dict)
    return False


def stage_affinity_score(stage: str, observation: Observation, looks_like_results_page: bool, has_searchbox: bool) -> int:
    text = f"{observation.url} {observation.title} {observation.text} {observation.visual_summary}".lower()
    extracted_fields = observation.extracted_fields if isinstance(observation.extracted_fields, dict) else {}
    score = 0
    if slot_signal_present_in_fields(stage, extracted_fields):
        score += 20
    if stage in LINK_SIGNAL_STAGES and isinstance(extracted_fields.get("links"), list) and extracted_fields.get("links"):
        score += 14
    if stage in DEEP_READ_SIGNAL_STAGES and isinstance(extracted_fields.get("deep_reads"), list) and extracted_fields.get("deep_reads"):
        score += 16
    if stage == "transcript_notes" and isinstance(extracted_fields.get("video_digest"), dict):
        score += 16
    if observation.url.lower().startswith("https://github.com") and stage in {"repo_candidates", "repo_metadata", "implementation_docs"}:
        score += 4
    if looks_like_results_page and stage in CANDIDATE_STAGES:
        score += 6
    if has_searchbox and stage in {"orientation", "candidate_pool", "repo_candidates", "video_candidates"}:
        score += 3
    score += sum(1 for token in STAGE_TEXT_CUES.get(stage, []) if token in text)
    return score


def stage_present_in_evidence(stage: str, evidence_text: str, observation: Observation | None = None) -> bool:
    if observation is not None and slot_signal_present_in_fields(stage, observation.extracted_fields if isinstance(observation.extracted_fields, dict) else {}):
        return True
    if stage == "candidate_pool":
        return any(token in evidence_text for token in ["candidate", "候选", "型号", "price", "价格"])
    return any(token in evidence_text for token in STAGE_TEXT_CUES.get(stage, []))


def stage_visible_on_current_page(
    stage: str,
    current_page_text: str,
    observation: Observation,
    looks_like_results_page: bool,
    has_searchbox: bool,
) -> bool:
    score = stage_affinity_score(stage, observation, looks_like_results_page, has_searchbox)
    if stage == "orientation":
        return bool(observation.title or observation.text or observation.visual_summary)
    if stage in DETAIL_STAGES and any(token in current_page_text for token in STAGE_TEXT_CUES.get(stage, [])):
        return True
    if score >= 8:
        return True
    if stage in CANDIDATE_STAGES:
        return looks_like_results_page or len(observation.elements or []) >= 1
    return False
