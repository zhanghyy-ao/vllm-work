from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import parse_qs, unquote_plus, urlparse

from browser_agent.types import Observation, WorkflowNode


def first_searchbox_ref(observation: Observation) -> Any:
    field_groups = [
        observation.form_fields or [],
        observation.accessibility_tree or [],
        observation.elements or [],
    ]
    for group in field_groups:
        for item in group:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").lower()
            tag = str(item.get("tag") or "").lower()
            name = f"{item.get('name', '')} {item.get('label', '')} {item.get('text', '')}".lower()
            if role in {"searchbox", "textbox", "combobox"}:
                return item.get("element_id", item.get("id"))
            if tag in {"input", "textarea"} and any(token in name for token in ["search", "搜索", "query", "keyword", "关键词"]):
                return item.get("element_id", item.get("id"))
    return None


def looks_like_results_page(observation: Observation) -> bool:
    parsed = urlparse(observation.url or "")
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if "bing.com" in host and ("/search" in path or "/videos/search" in path):
        return True
    if "github.com" in host and "/search" in path:
        return True
    if "arxiv.org" in host and "/search" in path:
        return True
    title_text = f"{observation.title} {observation.text[:500]}".lower()
    return any(term in title_text for term in ["search results", "搜索结果", "repositories", "论文", "视频搜索"])


def has_candidate_links(observation: Observation) -> bool:
    for item in observation.elements or []:
        if not isinstance(item, dict):
            continue
        href = str(item.get("href") or item.get("url") or "")
        if href.startswith("http://") or href.startswith("https://"):
            return True
    return False


def query_from_observation_url(observation: Observation) -> str:
    parsed = urlparse(observation.url or "")
    query = parse_qs(parsed.query).get("q") or parse_qs(parsed.query).get("query") or [""]
    return unquote_plus(str(query[0]))[:300]


def has_post_search_evidence_step(traces: List[Dict[str, Any]]) -> bool:
    seen_search = False
    for trace in traces:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        verdict = trace.get("verdict") if isinstance(trace.get("verdict"), dict) else {}
        action = node.get("action")
        if action == "search_web" and verdict.get("ok") is not False:
            seen_search = True
            continue
        if seen_search and action in {"collect_links", "open_candidate", "deep_read_candidates", "extract_page", "extract_video"}:
            return True
    return False


def has_deep_read_step(traces: List[Dict[str, Any]]) -> bool:
    for trace in traces:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        if node.get("action") in {"deep_read_candidates", "open_candidate", "extract_video"}:
            return True
    return False


def has_successful_deep_read(traces: List[Dict[str, Any]]) -> bool:
    for trace in traces:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        output = trace.get("output") if isinstance(trace.get("output"), dict) else {}
        verdict = trace.get("verdict") if isinstance(trace.get("verdict"), dict) else {}
        fields = output.get("fields") if isinstance(output.get("fields"), dict) else {}
        if node.get("action") != "deep_read_candidates" or verdict.get("ok") is False:
            continue
        deep_reads = fields.get("deep_reads") if isinstance(fields.get("deep_reads"), list) else []
        if deep_reads:
            return True
    return False


def has_successful_collect_links(traces: List[Dict[str, Any]]) -> bool:
    for trace in traces:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        output = trace.get("output") if isinstance(trace.get("output"), dict) else {}
        verdict = trace.get("verdict") if isinstance(trace.get("verdict"), dict) else {}
        fields = output.get("fields") if isinstance(output.get("fields"), dict) else {}
        if node.get("action") == "collect_links" and verdict.get("ok") is not False and isinstance(fields.get("links"), list) and fields["links"]:
            return True
    return False


def decision_repeats(node: WorkflowNode, traces: List[Dict[str, Any]]) -> bool:
    same = 0
    for trace in traces[-4:]:
        prior = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        prior_inputs = prior.get("inputs") if isinstance(prior.get("inputs"), dict) else {}
        if prior.get("action") != node.action:
            continue
        if node.action == "search_web" and prior_inputs.get("query") == node.inputs.get("query"):
            same += 1
        elif node.action in {"click_element", "type_text", "select_option"} and str(prior_inputs.get("element_ref")) == str(node.inputs.get("element_ref")):
            same += 1
        elif node.action in {"scroll", "wait", "extract_page"}:
            same += 1
        elif node.action == "summarize_text":
            same += 1
    return same >= 2


def repeated_search_like_behavior(node: WorkflowNode, traces: List[Dict[str, Any]]) -> bool:
    repeated = 0
    for trace in traces[-5:]:
        prior = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        prior_inputs = prior.get("inputs") if isinstance(prior.get("inputs"), dict) else {}
        if node.action == "search_web" and prior.get("action") == "search_web":
            if str(prior_inputs.get("query") or "").strip() == str(node.inputs.get("query") or "").strip():
                repeated += 1
        if node.action == "type_text" and prior.get("action") == "type_text":
            prior_text = str(prior_inputs.get("text") or "").strip()
            current_text = str(node.inputs.get("text") or "").strip()
            if prior_text and current_text and (prior_text == current_text or prior_text in current_text or current_text in prior_text):
                repeated += 1
    return repeated >= 1


def loop_state(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    visited_urls = []
    search_queries = []
    failed_actions = []
    for trace in traces:
        node = trace.get("node") if isinstance(trace.get("node"), dict) else {}
        inputs = node.get("inputs") if isinstance(node.get("inputs"), dict) else {}
        output = trace.get("output") if isinstance(trace.get("output"), dict) else {}
        verdict = trace.get("verdict") if isinstance(trace.get("verdict"), dict) else {}
        if output.get("url"):
            visited_urls.append(output["url"])
        if node.get("action") == "search_web" and inputs.get("query"):
            search_queries.append(inputs["query"])
        if verdict.get("ok") is False:
            failed_actions.append({"action": node.get("action"), "reason": output.get("error")})
    return {
        "visited_urls": _dedupe_strings(visited_urls)[-12:],
        "search_queries": _dedupe_strings(search_queries)[-8:],
        "failed_actions": failed_actions[-5:],
        "repeat_warning": "Avoid repeating visited URLs, identical queries, or failed actions unless new evidence is expected.",
    }


def current_page_capabilities(observation: Observation) -> Dict[str, Any]:
    return {
        "has_searchbox": first_searchbox_ref(observation) is not None,
        "looks_like_results_page": looks_like_results_page(observation),
        "has_candidate_links": has_candidate_links(observation),
        "visible_button_count": len(observation.visible_buttons or []),
        "form_field_count": len(observation.form_fields or []),
        "interactable_count": len(observation.elements or []),
    }


def low_quality_current_page(observation: Observation, target_stage: str = "") -> bool:
    haystack = f"{observation.url} {observation.title} {observation.text[:1600]} {observation.visual_summary}".lower()
    blocked_signals = [
        "gitcode.csdn.net",
        "devpress.csdn.net",
        "blog.csdn.net",
        "atomgit",
        "开源社区",
        "代码托管",
        "仓库镜像",
        "mirror",
        "转载",
        "登录后",
        "验证码",
        "访问异常",
    ]
    if any(token in haystack for token in blocked_signals):
        return True
    if target_stage == "comparative_reviews":
        review_signals = ["评测", "review", "对比", "compare", "优点", "缺点", "降噪", "续航", "通勤", "办公"]
        if not any(token in haystack for token in review_signals):
            return True
    if target_stage == "marketplace_pages":
        market_signals = ["商品", "参数", "价格", "price", "spec", "京东", "天猫", "淘宝", "amazon", "bestbuy"]
        if not any(token in haystack for token in market_signals):
            return True
    if target_stage == "user_comments":
        comment_signals = ["评论", "差评", "comment", "complaint", "issue", "problem", "评价"]
        if not any(token in haystack for token in comment_signals):
            return True
    return False


def supports_in_page_task_search(observation: Observation, source: str, page_query: str) -> bool:
    if first_searchbox_ref(observation) is None:
        return False
    if looks_like_results_page(observation):
        return False
    haystack = f"{observation.url} {observation.title} {observation.text[:1200]}".lower()
    query_terms = [
        token.lower()
        for token in page_query.replace("，", " ").replace(",", " ").split()
        if len(token.strip()) >= 2
    ]
    meaningful_hits = sum(1 for token in query_terms[:8] if token in haystack)
    generic_blockers = [
        "gitcode",
        "atomgit",
        "csdn",
        "open source community",
        "开源社区",
        "repository",
        "代码托管",
    ]
    if any(token in haystack for token in generic_blockers) and meaningful_hits == 0:
        return False
    if "github.com" in haystack or "search or jump to" in haystack:
        return True
    if source == "github":
        return "github.com" in haystack or "repository search" in haystack or "search or jump to" in haystack
    if source == "shopping":
        shopping_signals = ["耳机", "降噪", "评测", "对比", "推荐", "headphone", "review", "price", "价格", "商城", "商品"]
        return meaningful_hits >= 2 or any(signal in haystack for signal in shopping_signals)
    if source == "video":
        video_signals = ["video", "视频", "watch", "youtube", "bilibili", "教程", "字幕"]
        return meaningful_hits >= 1 or any(signal in haystack for signal in video_signals)
    if source == "paper":
        paper_signals = ["paper", "arxiv", "openreview", "论文", "scholar"]
        return meaningful_hits >= 1 or any(signal in haystack for signal in paper_signals)
    return meaningful_hits >= 1


def _dedupe_strings(values: List[Any]) -> List[str]:
    seen = set()
    out = []
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
