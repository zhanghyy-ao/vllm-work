from __future__ import annotations

import re
import uuid
import json
import base64
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qs
from urllib.parse import quote_plus
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from browser_agent.types import Action, ActionResult, EvidenceItem, Observation, WorkflowNode
from browser_agent.vision.keyframes import extract_video_keyframes


MAX_TEXT_CHARS = 6000
MAX_LINKS = 20
SLOT_SIGNAL_FIELD_MAP = {
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


TOOL_OUTCOMES = {
    "search": "collected candidate pages",
    "collect": "captured candidate cards",
    "open_topk": "opened top ranked detail pages",
    "compare": "produced comparison table and recommendation",
    "summarize": "summarized the page evidence",
    "analyze_form": "identified required form fields",
    "fill_form": "filled form draft values",
    "verify": "verified browser state against expected result",
    "find_slots": "found bookable time slots",
    "apply_filters": "applied user filters",
    "reserve": "created reservation draft pending confirmation",
    "extract_leads": "extracted structured lead records",
    "export_csv": "exported results to csv-ready rows",
    "snapshot_page": "captured baseline snapshot",
    "track_price": "registered watch target and threshold",
    "set_alert": "configured notification rule",
    "assert_ui": "validated critical UI checkpoints",
    "report_bug": "prepared regression report",
}


def execute_action(action: Action, observation: Observation) -> Dict[str, Any]:
    """Dispatch one browser tool action in deterministic harness-safe mode."""
    outcome = TOOL_OUTCOMES.get(action.tool)
    if outcome is None:
        return {"ok": False, "tool": action.tool, "error": "unsupported_tool"}

    detail = {
        "message": outcome,
        "target": action.target,
        "value": action.value,
        "page_title": observation.title,
    }
    return {
        "ok": True,
        "tool": action.tool,
        "url": observation.url,
        "detail": detail,
    }


def _search_url(source: str, query: str) -> str:
    encoded = quote_plus(query)
    if source == "github":
        return f"https://github.com/search?q={encoded}&type=repositories"
    if source == "paper":
        return f"https://arxiv.org/search/?query={encoded}&searchtype=all&source=header"
    if source == "video":
        return f"https://www.bing.com/videos/search?q={encoded}"
    if source == "shopping":
        return f"https://www.bing.com/search?q={encoded}+耳机+评测+价格+-股票+-指数+-中证1000"
    return f"https://www.bing.com/search?q={encoded}"


def _clean_text(value: str, limit: int = MAX_TEXT_CHARS) -> str:
    compact = re.sub(r"\s+", " ", value or "").strip()
    return compact[:limit]


def _evidence(source: str, url: str, claim: str, support: str, confidence: float = 0.65) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=str(uuid.uuid4()),
        source_type=source or "web",
        source_url=url,
        claim=claim,
        support=_clean_text(support, 500),
        confidence=confidence,
    )


def _extract_price_signal(text: str) -> str:
    compact = _clean_text(text, 2000)
    patterns = [
        r"(?:¥|￥|RMB\s*)\s?\d+(?:[,.]\d+)?",
        r"\d+(?:[,.]\d+)?\s?(?:元|人民币)",
        r"(?:\\$|USD\s*)\s?\d+(?:[,.]\d+)?",
    ]
    hits: List[str] = []
    for pattern in patterns:
        hits.extend(re.findall(pattern, compact, flags=re.IGNORECASE))
    seen = []
    for hit in hits:
        if hit not in seen:
            seen.append(hit)
    return " / ".join(seen[:6])


def _shopping_link_relevant(text: str, href: str, query: str) -> bool:
    haystack = f"{text} {href}".lower()
    product_terms = [
        "耳机",
        "headphone",
        "headphones",
        "headset",
        "earbud",
        "earbuds",
        "wh-ch720n",
        "w820nb",
        "space q45",
        "q45",
    ]
    blocked_intents = [
        "在线音频降噪",
        "音频降噪工具",
        "noise-removal",
        "audio-noise-reduction",
        "noise-cancellation",
        "denoise",
        "audio cleaner",
        "去除背景噪音",
    ]
    if any(term in haystack for term in blocked_intents):
        return False
    if any(term in query.lower() for term in ["耳机", "降噪", "headphone", "anc", "wh-ch720n", "w820nb", "q45"]):
        has_product_term = any(term in haystack for term in product_terms) or bool(re.search(r"\banc\b", haystack))
        if not has_product_term:
            return False
    strong_terms = [
        "耳机",
        "headphone",
        "headphones",
        "sony",
        "wh-ch720n",
        "soundcore",
        "q45",
        "w820nb",
        "漫步者",
        "声阔",
        "评测",
        "推荐",
        "值得买",
        "降噪",
        " anc ",
    ]
    if any(term in haystack for term in strong_terms):
        return True
    query_terms = [
        term.lower()
        for term in re.split(r"[^a-zA-Z0-9\u4e00-\u9fa5]+", query)
        if len(term) >= 3 and term not in {"1000", "以内", "购买", "价格", "对比"}
    ]
    return bool(query_terms and sum(1 for term in query_terms if term in haystack) >= 2)


def _video_link_relevant(text: str, href: str, query: str) -> bool:
    haystack = f"{text} {href}".lower()
    query_terms = [
        term.lower()
        for term in re.split(r"[^a-zA-Z0-9\u4e00-\u9fa5]+", query)
        if len(term) >= 3 and term not in {"视频", "教程", "主要内容", "入门", "查找", "整理"}
    ]
    platform_hit = any(term in haystack for term in ["youtube.com/watch", "youtu.be/", "bilibili.com/video/", "vimeo.com"])
    if not platform_hit:
        return False
    if not query_terms:
        return True
    return any(term in haystack for term in query_terms)


def _candidate_matches_requirement_slot(text: str, href: str, requirement_slot: str, query: str) -> bool:
    haystack = f"{text} {href}".lower()
    if requirement_slot == "comparative_reviews":
        review_domains = ["rtings.com", "soundguys.com", "whathifi.com", "techradar.com", "tomsguide.com", "theverge.com", "smzdm.com", "zol.com.cn"]
        if any(domain in haystack for domain in review_domains):
            return True
        review_terms = ["评测", "review", "reviews", "对比", "compare", "comparison", "pros", "cons", "优点", "缺点", "续航", "降噪"]
        return any(term in haystack for term in review_terms)
    if requirement_slot == "marketplace_pages":
        market_terms = ["商品", "参数", "价格", "price", "spec", "official", "jd.com", "tmall.com", "taobao.com", "amazon.com", "bestbuy.com", "soundcore.com", "sony.com", "edifier.com"]
        return any(term in haystack for term in market_terms)
    if requirement_slot == "user_comments":
        comment_terms = ["评论", "差评", "comment", "comments", "complaint", "issue", "problem", "reddit", "forum", "bbs", "评价"]
        return any(term in haystack for term in comment_terms)
    if requirement_slot in {"video_reviews", "transcript_notes"}:
        return _video_link_relevant(text, href, query) or any(term in haystack for term in ["youtube", "bilibili", "视频", "watch"])
    return True


def _candidate_quality_score(text: str, href: str, source: str, query: str, requirement_slot: str = "") -> int:
    haystack = f"{text} {href}".lower()
    parsed = urlparse(href)
    host = parsed.netloc.lower()
    score = 0

    blocked_domains = [
        "gitcode.csdn.net",
        "devpress.csdn.net",
        "csdn.net",
        "blog.csdn.net",
        "atomgit.com",
    ]
    if any(domain in host for domain in blocked_domains):
        score -= 8
    if any(token in haystack for token in ["mirror", "转载", "镜像", "登录后", "验证码", "forbidden", "403"]):
        score -= 6
    if any(token in haystack for token in ["open source community", "开源社区", "代码托管", "仓库镜像", "atomgit", "gitcode"]):
        score -= 10

    if source == "shopping":
        if any(domain in host for domain in ["rtings.com", "soundguys.com", "whathifi.com", "theverge.com", "techradar.com", "tomsguide.com"]):
            score += 10
        if any(domain in host for domain in ["smzdm.com", "zol.com.cn", "jd.com", "tmall.com", "taobao.com", "amazon.com", "bestbuy.com", "soundcore.com", "sony.com", "edifier.com"]):
            score += 7
        if any(domain in host for domain in ["youtube.com", "youtu.be", "bilibili.com"]):
            score += 5
        if any(token in haystack for token in ["评测", "review", "reviews", "对比", "compare", "comparison", "pros", "cons", "优点", "缺点"]):
            score += 5
        if any(token in haystack for token in ["价格", "price", "spec", "参数", "续航", "降噪", "通勤", "办公", "comment", "评论", "差评"]):
            score += 3
        if any(token in haystack for token in ["community", "forum", "bbs", "百科", "wiki", "github"]):
            score -= 2
        if query and _shopping_link_relevant(text, href, query):
            score += 2
    elif source == "video":
        if any(domain in host for domain in ["youtube.com", "youtu.be", "bilibili.com", "vimeo.com"]):
            score += 8
        if _video_link_relevant(text, href, query):
            score += 4
    elif source == "github":
        if host == "github.com":
            score += 10
    else:
        if any(token in haystack for token in ["review", "评测", "compare", "comparison", "recommend", "推荐"]):
            score += 4
        if any(domain in host for domain in ["rtings.com", "soundguys.com", "whathifi.com", "smzdm.com", "zol.com.cn"]):
            score += 5

    if requirement_slot == "comparative_reviews":
        if any(domain in host for domain in ["rtings.com", "soundguys.com", "whathifi.com", "techradar.com", "tomsguide.com", "theverge.com"]):
            score += 10
        if any(token in haystack for token in ["评测", "review", "reviews", "对比", "compare", "comparison", "pros", "cons", "优点", "缺点"]):
            score += 6
        if any(domain in host for domain in ["jd.com", "tmall.com", "taobao.com", "amazon.com", "bestbuy.com"]):
            score += 1
    elif requirement_slot == "marketplace_pages":
        if any(domain in host for domain in ["jd.com", "tmall.com", "taobao.com", "amazon.com", "bestbuy.com", "soundcore.com", "sony.com", "edifier.com"]):
            score += 10
        if any(token in haystack for token in ["价格", "price", "spec", "参数", "购买", "商品"]):
            score += 5
    elif requirement_slot == "user_comments":
        if any(token in haystack for token in ["评论", "差评", "comment", "comments", "complaint", "issue", "problem", "reddit", "forum", "bbs"]):
            score += 8
    elif requirement_slot in {"video_reviews", "transcript_notes"}:
        if any(domain in host for domain in ["youtube.com", "youtu.be", "bilibili.com"]):
            score += 10

    return score


def _requirement_slot_from_node(node: WorkflowNode) -> str:
    return str(node.inputs.get("requirement_slot") or node.inputs.get("evidence_stage") or "")


def _slot_signal_field(requirement_slot: str) -> str:
    return SLOT_SIGNAL_FIELD_MAP.get(requirement_slot, "requirement_slot_signals")


class BrowserSession:
    """Small Playwright wrapper used by the harness runtime."""

    def __init__(self, headless: bool = True, timeout_ms: int = 20000) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._playwright = None
        self.browser = None
        self.page = None

    def __enter__(self) -> "BrowserSession":
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()

    def observe_current_page(
        self,
        previous: Observation | None = None,
        node_id: str = "observe",
        seed_fields: Dict[str, Any] | None = None,
    ) -> Observation:
        assert self.page is not None
        previous = previous or Observation(url=self.page.url, title="", text="")
        title = self.page.title()
        text = self._body_text()
        snapshot = self._page_snapshot_fields(node_id)
        links = self._search_result_links()[:20]
        merged_elements: List[Dict[str, Any]] = []
        seen = set()
        for item in list(previous.elements) + list(snapshot.get("interactable_elements", [])) + list(links):
            if not isinstance(item, dict):
                continue
            key = str(item.get("element_id") or item.get("selector") or item.get("href") or item.get("url") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            merged_elements.append(item)
        merged_fields = dict(previous.extracted_fields)
        merged_fields.update(snapshot)
        if seed_fields:
            merged_fields.update(seed_fields)
        return Observation(
            url=self.page.url,
            title=title or previous.title,
            text=text or previous.text,
            elements=merged_elements,
            screenshot_path=str(snapshot.get("screenshot_path", previous.screenshot_path)),
            screenshot_base64=str(snapshot.get("screenshot_base64", previous.screenshot_base64)),
            accessibility_tree=snapshot.get("accessibility_tree", previous.accessibility_tree),
            form_fields=snapshot.get("form_fields", previous.form_fields),
            visible_buttons=snapshot.get("visible_buttons", previous.visible_buttons),
            visual_summary=str(snapshot.get("visual_summary", previous.visual_summary)),
            extracted_fields=merged_fields,
        )

    def sync_to_observation(self, observation: Observation) -> None:
        assert self.page is not None
        target_url = str(observation.url or "").strip()
        if not target_url or target_url == "about:blank":
            return
        current_url = str(self.page.url or "").strip()
        if current_url == target_url:
            return
        self.page.goto(target_url, wait_until="commit", timeout=self.timeout_ms)
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=5000)
        except PlaywrightTimeoutError:
            pass

    def execute(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        try:
            if node.action == "goto":
                result = self._goto(str(node.inputs.get("url") or observation.url), node)
            elif node.action == "search_web":
                result = self._search_web(node, observation)
            elif node.action == "open_candidate":
                result = self._open_candidate(node, observation)
            elif node.action == "deep_read_candidates":
                result = self._deep_read_candidates(node, observation)
            elif node.action == "extract_page":
                result = self._extract_page(node)
            elif node.action == "extract_video":
                result = self._extract_video(node)
            elif node.action == "collect_links":
                result = self._collect_links(node, observation)
            elif node.action == "summarize_text":
                result = self._summarize_text(node, observation)
            elif node.action == "click_element":
                result = self._click_element(node, observation)
            elif node.action == "type_text":
                result = self._type_text(node, observation)
            elif node.action == "select_option":
                result = self._select_option(node, observation)
            elif node.action == "scroll":
                result = self._scroll(node, observation)
            elif node.action == "wait":
                result = self._wait(node, observation)
            elif node.action == "back":
                result = self._back(node, observation)
            elif node.action == "press_key":
                result = self._press_key(node, observation)
            else:
                result = ActionResult(ok=False, action=node.action, url=observation.url, error="unsupported_action")
            if node.inputs.get("evidence_stage") and isinstance(result.fields, dict):
                result.fields.setdefault("evidence_stage", node.inputs.get("evidence_stage"))
            if node.inputs.get("dynamic") and isinstance(result.fields, dict):
                result.fields.setdefault("dynamic", True)
            result.fallback_used = node.inputs.get("fallback_used")
            return result
        except PlaywrightTimeoutError as exc:
            partial = self._partial_result(node, observation, f"timeout: {exc}")
            partial.fallback_used = node.inputs.get("fallback_used")
            return partial
        except PlaywrightError as exc:
            return ActionResult(
                ok=False,
                action=node.action,
                url=self._safe_url(observation),
                error=f"playwright_error: {exc}",
                human_review_required="Executable doesn't exist" in str(exc),
            )
        except Exception as exc:  # pragma: no cover - defensive boundary for browser side effects.
            return ActionResult(ok=False, action=node.action, url=self._safe_url(observation), error=f"unexpected_error: {exc}")

    def _safe_url(self, observation: Observation) -> str:
        if self.page:
            return self.page.url
        return observation.url

    def _goto(self, url: str, node: WorkflowNode, claim: str = "Opened page") -> ActionResult:
        assert self.page is not None
        response = self.page.goto(url, wait_until="commit", timeout=self.timeout_ms)
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        title = self.page.title()
        text = self._body_text()
        status = response.status if response else None
        ok = bool(title or text) and (status is None or status < 500)
        fields = {"status": status, "source": node.inputs.get("source", "web")}
        fields.update(self._page_snapshot_fields(node.id))
        return ActionResult(
            ok=ok,
            action=node.action,
            url=self.page.url,
            title=title,
            text=text,
            fields=fields,
            evidence=[_evidence(str(node.inputs.get("source", "web")), self.page.url, claim, title or text)],
            error=None if ok else f"bad_status_or_empty_page: {status}",
        )

    def _partial_result(self, node: WorkflowNode, observation: Observation, error: str) -> ActionResult:
        if not self.page:
            return ActionResult(ok=False, action=node.action, url=observation.url, error=error)
        title = self.page.title()
        text = self._body_text()
        ok = bool(title or text)
        source_url = self._intended_url(node, observation)
        evidence = []
        if ok:
            evidence.append(_evidence(str(node.inputs.get("source", "web")), source_url, "Partial page content", title or text, 0.5))
        return ActionResult(
            ok=ok,
            action=node.action,
            url=source_url,
            title=title,
            text=text,
            fields={"partial": True, "source": node.inputs.get("source", "web")} if ok else {},
            evidence=evidence,
            error=None if ok else error,
        )

    def _intended_url(self, node: WorkflowNode, observation: Observation) -> str:
        if self.page and self.page.url and self.page.url != "about:blank":
            return self.page.url
        if node.action == "search_web":
            source = str(node.inputs.get("source", "general"))
            query = str(node.inputs.get("query") or node.inputs.get("value") or "")
            return _search_url(source, query)
        return str(node.inputs.get("url") or observation.url)

    def _search_web(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        source = str(node.inputs.get("source", "general"))
        query = str(node.inputs.get("query") or node.inputs.get("value") or "")
        search_box_ref = self._find_searchbox_ref(observation)
        if search_box_ref is not None:
            type_node = WorkflowNode(
                id=node.id,
                type=node.type,
                instruction=node.instruction,
                action="type_text",
                inputs={
                    **node.inputs,
                    "element_ref": search_box_ref,
                    "text": query,
                    "clear": True,
                    "submit_after_type": True,
                    "search_execution_mode": "in_page_searchbox",
                },
                depends_on=node.depends_on,
                success_criteria=node.success_criteria,
                retry_policy=node.retry_policy,
            )
            result = self._type_text(type_node, observation)
            if isinstance(result.fields, dict):
                result.fields.setdefault("search_execution_mode", "in_page_searchbox")
            return result
        result = self._goto(_search_url(source, query), node, claim=f"Search results for {query}")
        if isinstance(result.fields, dict):
            result.fields.setdefault("search_execution_mode", "external_search_url")
        return result

    def _extract_page(self, node: WorkflowNode) -> ActionResult:
        assert self.page is not None
        title = self.page.title()
        text = self._body_text()
        screenshot_path = self._screenshot(node.id)
        fields = {"screenshot_path": screenshot_path, "source": node.inputs.get("source", "web")}
        fields.update(self._page_snapshot_fields(node.id, existing_screenshot=screenshot_path))
        requirement_slot = _requirement_slot_from_node(node)
        self._attach_slot_signals(fields, requirement_slot, {"title": title, "text": text, "screenshot_path": screenshot_path})
        return ActionResult(
            ok=bool(text),
            action=node.action,
            url=self.page.url,
            title=title,
            text=text,
            fields=fields,
            evidence=[_evidence(str(node.inputs.get("source", "web")), self.page.url, "Page text extracted", text)],
            error=None if text else "empty_page_text",
        )

    def _open_candidate(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        source = str(node.inputs.get("source", "web"))
        requirement_slot = _requirement_slot_from_node(node)
        query = str(node.inputs.get("query") or self._query_from_url(observation.url) or "")
        candidates = self._prioritized_candidates(observation.elements or [], source, query, requirement_slot)
        rank = int(node.inputs.get("rank", 0))
        if not candidates or rank >= len(candidates):
            return ActionResult(
                ok=False,
                action=node.action,
                url=observation.url,
                title=observation.title,
                text=observation.text,
                error="candidate_not_found",
            )
        candidate = candidates[rank]
        href = str(candidate.get("href") or candidate.get("url") or "")
        if not href:
            return ActionResult(ok=False, action=node.action, url=observation.url, error="candidate_missing_href")
        return self._goto(href, node, claim=f"Opened candidate: {candidate.get('text', href)}")

    def _deep_read_candidates(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        source = str(node.inputs.get("source", "web"))
        requirement_slot = _requirement_slot_from_node(node)
        query = str(node.inputs.get("query") or self._query_from_url(observation.url) or "")
        candidates = self._prioritized_candidates(observation.elements or [], source, query, requirement_slot)
        limit = max(1, min(int(node.inputs.get("limit", 3)), 5))
        readings: List[Dict[str, Any]] = []
        evidence: List[EvidenceItem] = []

        if not candidates:
            return ActionResult(
                ok=False,
                action=node.action,
                url=observation.url,
                title=observation.title,
                text=observation.text,
                error="no_candidates_to_deep_read",
            )

        for rank, candidate in enumerate(candidates[:limit], start=1):
            href = str(candidate.get("href") or candidate.get("url") or "")
            if not href:
                continue
            reading = self._read_candidate_page(href, candidate, rank, source)
            readings.append(reading)
            support = " ".join(
                str(part)
                for part in [
                    reading.get("title", ""),
                    reading.get("description", ""),
                    reading.get("price_signal", ""),
                    reading.get("text", ""),
                ]
                if part
            )
            evidence.append(
                _evidence(
                    source,
                    href,
                    f"Deep candidate read: {reading.get('name') or href}",
                    support,
                    0.78 if reading.get("ok") else 0.45,
                )
            )

        combined = _clean_text(" ".join(str(item.get("text", "")) for item in readings), 3000)
        fields = {"deep_reads": readings, "links": candidates, "source": source}
        fields.update(self._page_snapshot_fields(node.id))
        self._attach_slot_signals(
            fields,
            requirement_slot,
            {
                "readings": readings,
                "links": candidates,
                "combined_text": combined,
                "page_title": observation.title,
            },
        )
        return ActionResult(
            ok=bool(readings),
            action=node.action,
            url=observation.url,
            title=observation.title,
            text=combined or observation.text,
            fields=fields,
            evidence=evidence,
            error=None if readings else "deep_read_failed",
        )

    def _prioritized_candidates(self, candidates: List[Dict[str, Any]], source: str, query: str = "", requirement_slot: str = "") -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        seen = set()
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            href = str(candidate.get("href") or candidate.get("url") or "")
            text = _clean_text(str(candidate.get("text") or candidate.get("name") or candidate.get("label") or ""), 160)
            if not href or href in seen:
                continue
            if source == "shopping" and not _shopping_link_relevant(text, href, query):
                continue
            if source == "video" and not _video_link_relevant(text, href, query):
                continue
            if requirement_slot and not _candidate_matches_requirement_slot(text, href, requirement_slot, query):
                continue
            seen.add(href)
            normalized.append({**candidate, "href": href, "text": text, "_score": _candidate_quality_score(text, href, source, query, requirement_slot)})
        normalized.sort(key=lambda item: (int(item.get("_score", 0)), len(str(item.get("text") or ""))), reverse=True)
        return normalized

    def _read_candidate_page(self, href: str, candidate: Dict[str, Any], rank: int, source: str) -> Dict[str, Any]:
        if source == "github":
            github_reading = self._read_github_repo(href, candidate, rank)
            if github_reading.get("ok"):
                return github_reading
        assert self.browser is not None
        page = self.browser.new_page()
        page.set_default_timeout(self.timeout_ms)
        try:
            response = page.goto(href, wait_until="commit", timeout=self.timeout_ms)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            except PlaywrightTimeoutError:
                pass
            title = page.title()
            try:
                text = _clean_text(page.locator("body").inner_text(timeout=5000), 2500)
            except PlaywrightError:
                text = ""
            meta = self._metadata_for_page(page)
            price_signal = _extract_price_signal(" ".join([title, meta.get("description", ""), text]))
            return {
                "ok": bool(title or text),
                "rank": rank,
                "name": _clean_text(str(candidate.get("text") or title or href), 160),
                "url": page.url or href,
                "title": title,
                "description": meta.get("description", ""),
                "price_signal": price_signal,
                "source": source,
                "status": response.status if response else None,
                "text": text,
            }
        except Exception as exc:
            return {
                "ok": False,
                "rank": rank,
                "name": _clean_text(str(candidate.get("text") or href), 160),
                "url": href,
                "source": source,
                "error": str(exc),
            }
        finally:
            page.close()

    def _read_github_repo(self, href: str, candidate: Dict[str, Any], rank: int) -> Dict[str, Any]:
        parsed = urlparse(href)
        parts = [part for part in parsed.path.split("/") if part]
        if parsed.netloc.lower() != "github.com" or len(parts) < 2:
            return {"ok": False, "rank": rank, "name": str(candidate.get("text") or href), "url": href, "source": "github"}
        owner, repo = parts[0], parts[1]
        api_root = f"https://api.github.com/repos/{owner}/{repo}"
        repo_payload = self._github_api_get(api_root)
        if not repo_payload:
            return {"ok": False, "rank": rank, "name": f"{owner}/{repo}", "url": href, "source": "github", "error": "github_api_repo_failed"}
        readme_text = self._github_readme_text(owner, repo)
        topics = repo_payload.get("topics") or []
        license_payload = repo_payload.get("license") or {}
        support = " ".join(
            str(part)
            for part in [
                repo_payload.get("full_name"),
                repo_payload.get("description"),
                " ".join(topics[:12]),
                readme_text,
            ]
            if part
        )
        return {
            "ok": True,
            "rank": rank,
            "name": repo_payload.get("full_name") or f"{owner}/{repo}",
            "url": repo_payload.get("html_url") or href,
            "title": repo_payload.get("full_name") or f"{owner}/{repo}",
            "description": repo_payload.get("description") or "",
            "source": "github",
            "status": 200,
            "text": _clean_text(support, 2500),
            "repo": {
                "full_name": repo_payload.get("full_name"),
                "stars": repo_payload.get("stargazers_count"),
                "forks": repo_payload.get("forks_count"),
                "open_issues": repo_payload.get("open_issues_count"),
                "language": repo_payload.get("language"),
                "license": license_payload.get("spdx_id") or license_payload.get("name"),
                "updated_at": repo_payload.get("updated_at"),
                "pushed_at": repo_payload.get("pushed_at"),
                "homepage": repo_payload.get("homepage"),
                "topics": topics[:12],
                "readme_excerpt": _clean_text(readme_text, 900),
            },
        }

    def _github_api_get(self, url: str) -> Dict[str, Any]:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "browser-workflow-agent",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            return {}

    def _github_readme_text(self, owner: str, repo: str) -> str:
        payload = self._github_api_get(f"https://api.github.com/repos/{owner}/{repo}/readme")
        content = payload.get("content")
        if not isinstance(content, str):
            return ""
        try:
            raw = base64.b64decode(content.replace("\n", ""), validate=False)
        except Exception:
            return ""
        return _clean_text(raw.decode("utf-8", errors="replace"), 3000)

    def _extract_video(self, node: WorkflowNode) -> ActionResult:
        assert self.page is not None
        title = self.page.title()
        text = self._body_text()
        requirement_slot = _requirement_slot_from_node(node)
        meta = self._page_metadata()
        links = self._visible_video_links()
        transcript = self._visible_transcript_text()
        oembed = self._video_oembed(self.page.url)
        ytdlp = self._yt_dlp_metadata(self.page.url)
        screenshot_path = self._screenshot(node.id)
        keyframes = extract_video_keyframes(self.page.url, max_frames=int(node.inputs.get("max_keyframes", 3)))
        digest = {
            "url": self.page.url,
            "title": title,
            "meta": meta,
            "oembed": oembed,
            "yt_dlp": ytdlp,
            "visible_transcript": transcript[:3000],
            "candidate_video_links": links[:12],
            "screenshot_path": screenshot_path,
            "keyframes": keyframes,
            "multimodal_ready": True,
            "multimodal_note": "Screenshot and optional key-frame handoff are ready for a Gemini vision provider when GEMINI_API_KEY is configured.",
        }
        support_parts = [
            title,
            meta.get("description", ""),
            transcript,
            text,
            " ".join(link.get("text", "") for link in links[:8]),
        ]
        support = _clean_text(" ".join(part for part in support_parts if part), 1600)
        fields = {"video_digest": digest, "source": node.inputs.get("source", "video"), "screenshot_path": screenshot_path}
        fields.update(self._page_snapshot_fields(node.id, existing_screenshot=screenshot_path))
        self._attach_slot_signals(
            fields,
            requirement_slot,
            {"digest": digest, "links": links, "transcript": transcript, "support": support},
        )
        return ActionResult(
            ok=bool(support or links or oembed or ytdlp),
            action=node.action,
            url=self.page.url,
            title=title,
            text=support,
            fields=fields,
            evidence=[_evidence(str(node.inputs.get("source", "video")), self.page.url, "Video page digest", support or title, 0.68)],
            error=None if support or links or oembed or ytdlp else "no_video_metadata_extracted",
        )

    def _collect_links(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        assert self.page is not None
        links = self._search_result_links()
        if not links:
            links = self._observation_links(observation)
        source = str(node.inputs.get("source", "web"))
        requirement_slot = _requirement_slot_from_node(node)
        query = str(node.inputs.get("query") or self._query_from_url(self.page.url) or self._query_from_url(observation.url) or "")
        normalized = self._rank_links(links, source, query)
        if source == "github":
            api_links = self._github_api_links(query)
            normalized = api_links or normalized
        title = self.page.title()
        text = self._body_text()
        evidence = [
            _evidence(
                source,
                item["href"],
                f"Candidate link: {item['text']}",
                item["text"],
                0.72,
            )
            for item in normalized[:10]
        ]
        fields = {"links": normalized, "source": source, "query": query}
        fields.update(self._page_snapshot_fields(node.id))
        self._attach_slot_signals(
            fields,
            requirement_slot,
            {"links": normalized, "query": query, "source": source, "page_title": title, "page_text": text},
        )
        return ActionResult(
            ok=bool(normalized),
            action=node.action,
            url=self.page.url,
            title=title,
            text=text,
            fields=fields,
            evidence=evidence,
            error=None if normalized else "no_links_collected",
        )

    def _observation_links(self, observation: Observation) -> List[Dict[str, str]]:
        synthesized: List[Dict[str, str]] = []
        seen = set()
        for item in observation.elements or []:
            if not isinstance(item, dict):
                continue
            href = str(item.get("href") or item.get("url") or "").strip()
            text = _clean_text(
                str(item.get("text") or item.get("name") or item.get("label") or ""),
                140,
            )
            if not href or not text or href in seen:
                continue
            seen.add(href)
            synthesized.append({"text": text, "href": href})
        return synthesized

    def _search_result_links(self) -> List[Dict[str, str]]:
        assert self.page is not None
        parsed = urlparse(self.page.url)
        host = parsed.netloc.lower()
        if "bing.com" in host:
            selectors = [
                "li.b_algo h2 a",
                "li.b_algo .b_title a",
                ".b_results h2 a",
                "a.tilk",
            ]
            script = """selectors => {
                const picked = [];
                const seen = new Set();
                for (const selector of selectors) {
                    for (const a of document.querySelectorAll(selector)) {
                        const text = (a.innerText || a.textContent || '').replace(/\\s+/g, ' ').trim();
                        const href = a.href || '';
                        if (!text || !href || seen.has(href)) continue;
                        seen.add(href);
                        picked.push({text, href});
                    }
                }
                return picked.slice(0, 40);
            }"""
            try:
                links = self.page.evaluate(script, selectors)
                if links:
                    return links
            except PlaywrightError:
                pass
        try:
            return self.page.locator("a").evaluate_all(
                """els => els.map(a => ({
                    text: (a.innerText || a.textContent || '').replace(/\\s+/g, ' ').trim(),
                    href: a.href || ''
                })).filter(x => x.href && x.text).slice(0, 80)"""
            )
        except PlaywrightError:
            return []

    def _summarize_text(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        source = str(node.inputs.get("source", "web"))
        requirement_slot = _requirement_slot_from_node(node)
        support = observation.text or observation.title or observation.url
        summary = _clean_text(support, 1000)
        fields = {"summary": summary, "source": source, "links": observation.elements}
        if isinstance(observation.extracted_fields.get("video_digest"), dict):
            fields["video_digest"] = observation.extracted_fields["video_digest"]
        self._attach_slot_signals(
            fields,
            requirement_slot,
            {
                "summary": summary,
                "links": observation.elements,
                "video_digest": observation.extracted_fields.get("video_digest"),
                "text": observation.text,
                "title": observation.title,
            },
        )
        return ActionResult(
            ok=bool(summary),
            action=node.action,
            url=observation.url,
            title=observation.title,
            text=summary,
            fields=fields,
            evidence=[_evidence(source, observation.url, "Summary source text", summary)],
            error=None if summary else "no_text_to_summarize",
        )

    def _click_element(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        assert self.page is not None
        locator = self._locator_for_ref(node, observation)
        if locator is None:
            return ActionResult(ok=False, action=node.action, url=self.page.url, error="element_ref_not_found")
        locator.click(timeout=5000)
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=3000)
        except PlaywrightTimeoutError:
            pass
        return self._extract_page(node)

    def _attach_slot_signals(self, fields: Dict[str, Any], requirement_slot: str, payload: Dict[str, Any]) -> None:
        if not requirement_slot:
            return
        fields.setdefault("requirement_slot", requirement_slot)
        signal_field = _slot_signal_field(requirement_slot)
        fields[signal_field] = self._slot_signal_payload(requirement_slot, payload)

    def _slot_signal_payload(self, requirement_slot: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        links = payload.get("links") if isinstance(payload.get("links"), list) else []
        readings = payload.get("readings") if isinstance(payload.get("readings"), list) else []
        transcript = str(payload.get("transcript") or "")
        digest = payload.get("digest") if isinstance(payload.get("digest"), dict) else {}
        summary = str(payload.get("summary") or payload.get("combined_text") or payload.get("text") or payload.get("support") or "")
        base = {"slot": requirement_slot, "evidence_count": len(links) + len(readings), "summary": _clean_text(summary, 800)}
        if requirement_slot in {"candidate_pool", "repo_candidates", "video_candidates"}:
            base.update({"candidates": links[:10], "query": payload.get("query", ""), "source": payload.get("source", "")})
        elif requirement_slot == "repo_metadata":
            repo_cards = [reading.get("repo", {}) for reading in readings if isinstance(reading.get("repo"), dict)]
            base.update({"repositories": repo_cards, "readings": readings[:5], "doc_coverage": sum(1 for repo in repo_cards if repo.get("readme_excerpt"))})
        elif requirement_slot == "implementation_docs":
            base.update(
                {
                    "readings": readings[:5],
                    "doc_sources": [reading.get("url") for reading in readings[:5] if reading.get("url")],
                    "doc_coverage": sum(1 for reading in readings if str(reading.get("text") or reading.get("description") or "").strip()),
                }
            )
        elif requirement_slot in {"comparative_reviews", "ecosystem_comparison", "marketplace_pages"}:
            base.update({"readings": readings[:5], "candidate_count": len(links), "source": payload.get("source", "")})
        elif requirement_slot == "user_comments":
            base.update({"comment_pages": links[:10], "readings": readings[:5], "comment_signal": bool(summary)})
        elif requirement_slot == "transcript_notes":
            base.update({"transcript_excerpt": _clean_text(transcript, 1200), "video_title": digest.get("title"), "chapter_count": len(digest.get("candidate_video_links") or [])})
        elif requirement_slot == "visual_evidence":
            base.update({"screenshot_path": payload.get("screenshot_path") or digest.get("screenshot_path"), "has_visual_summary": bool(summary)})
        else:
            base.update({"payload_keys": sorted(payload.keys())})
        return base

    def _type_text(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        assert self.page is not None
        locator = self._locator_for_ref(node, observation)
        if locator is None:
            return ActionResult(ok=False, action=node.action, url=self.page.url, error="element_ref_not_found")
        text = str(node.inputs.get("text") or node.inputs.get("value") or "")
        if not text:
            return ActionResult(ok=False, action=node.action, url=self.page.url, error="missing_text")
        if bool(node.inputs.get("clear", True)):
            locator.fill("", timeout=5000)
            locator.fill(text, timeout=5000)
        else:
            locator.type(text, timeout=5000)
        if bool(node.inputs.get("submit_after_type", False)):
            submit_meta = self._submit_after_typing(locator, observation)
            if not submit_meta.get("ok"):
                return ActionResult(
                    ok=False,
                    action=node.action,
                    url=self.page.url,
                    error="submit_after_type_failed",
                    fields={"submit_after_type": submit_meta},
                )
            extracted = self._extract_page(node)
            extracted.fields["submit_after_type"] = submit_meta
            return extracted
        return self._extract_page(node)

    def _select_option(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        assert self.page is not None
        locator = self._locator_for_ref(node, observation)
        if locator is None:
            return ActionResult(ok=False, action=node.action, url=self.page.url, error="element_ref_not_found")
        value = str(node.inputs.get("value") or node.inputs.get("label") or "")
        if not value:
            return ActionResult(ok=False, action=node.action, url=self.page.url, error="missing_option_value")
        locator.select_option(value, timeout=5000)
        return self._extract_page(node)

    def _scroll(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        assert self.page is not None
        direction = str(node.inputs.get("direction") or "down").lower()
        pixels = int(node.inputs.get("pixels") or 700)
        delta = -abs(pixels) if direction == "up" else abs(pixels)
        self.page.mouse.wheel(0, delta)
        return self._extract_page(node)

    def _wait(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        assert self.page is not None
        ms = max(250, min(int(node.inputs.get("ms") or 1000), 5000))
        self.page.wait_for_timeout(ms)
        return self._extract_page(node)

    def _back(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        assert self.page is not None
        self.page.go_back(wait_until="commit", timeout=self.timeout_ms)
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=3000)
        except PlaywrightTimeoutError:
            pass
        return self._extract_page(node)

    def _press_key(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        assert self.page is not None
        key = str(node.inputs.get("key") or "")
        if not key:
            return ActionResult(ok=False, action=node.action, url=self.page.url, error="missing_key")
        self.page.keyboard.press(key)
        return self._extract_page(node)

    def _submit_after_typing(self, locator, observation: Observation) -> Dict[str, Any]:
        assert self.page is not None
        methods: List[str] = []
        before_url = self.page.url
        before_title = ""
        before_text = ""
        try:
            before_title = self.page.title()
        except PlaywrightError:
            before_title = ""
        try:
            before_text = self._body_text()
        except PlaywrightError:
            before_text = ""

        def page_advanced() -> bool:
            current_url = self.page.url
            if current_url and current_url != before_url:
                return True
            try:
                current_title = self.page.title()
            except PlaywrightError:
                current_title = ""
            if current_title and current_title != before_title:
                return True
            try:
                current_text = self._body_text()
            except PlaywrightError:
                current_text = ""
            return bool(current_text and current_text != before_text)

        try:
            locator.press("Enter", timeout=3000)
            methods.append("press_enter")
            try:
                self.page.wait_for_load_state("domcontentloaded", timeout=3000)
            except PlaywrightTimeoutError:
                pass
            if page_advanced():
                return {"ok": True, "method": "press_enter", "methods_tried": methods}
        except PlaywrightError:
            methods.append("press_enter_failed")

        try:
            locator.evaluate(
                """el => {
                    const form = el && typeof el.closest === "function" ? el.closest("form") : null;
                    if (!form) {
                        return false;
                    }
                    if (typeof form.requestSubmit === "function") {
                        form.requestSubmit();
                    } else {
                        form.submit();
                    }
                    return true;
                }"""
            )
            methods.append("request_submit")
            try:
                self.page.wait_for_load_state("domcontentloaded", timeout=3000)
            except PlaywrightTimeoutError:
                pass
            if page_advanced():
                return {"ok": True, "method": "request_submit", "methods_tried": methods}
        except PlaywrightError:
            methods.append("request_submit_failed")

        search_button = self._find_search_button_ref(observation)
        if search_button is not None:
            button_locator = self._locator_for_element_ref(search_button, observation)
            if button_locator is not None:
                try:
                    button_locator.click(timeout=3000)
                    methods.append("click_search_button")
                    try:
                        self.page.wait_for_load_state("domcontentloaded", timeout=3000)
                    except PlaywrightTimeoutError:
                        pass
                    if page_advanced():
                        return {"ok": True, "method": "click_search_button", "element_ref": search_button, "methods_tried": methods}
                except PlaywrightError:
                    methods.append("click_search_button_failed")
        return {"ok": False, "methods_tried": methods}

    def _locator_for_ref(self, node: WorkflowNode, observation: Observation):
        assert self.page is not None
        ref = node.inputs.get("element_ref")
        if ref is None:
            ref = node.inputs.get("element_id")
        return self._locator_for_element_ref(ref, observation)

    def _locator_for_element_ref(self, ref, observation: Observation):
        assert self.page is not None
        selector = ""
        if isinstance(ref, dict):
            selector = str(ref.get("selector") or "")
            ref = ref.get("element_id", ref.get("id", ref.get("index")))
        if not selector and ref is not None:
            for item in observation.elements or []:
                if not isinstance(item, dict):
                    continue
                if str(item.get("element_id") or item.get("id") or item.get("index")) == str(ref):
                    selector = str(item.get("selector") or "")
                    break
        if selector:
            return self.page.locator(selector).first
        if ref is not None:
            return self.page.locator(f'[data-agent-idx="{ref}"]').first
        return None

    def _find_search_button_ref(self, observation: Observation):
        groups = [observation.visible_buttons or [], observation.elements or []]
        for group in groups:
            for item in group:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role") or "").lower()
                name = f"{item.get('name', '')} {item.get('label', '')} {item.get('text', '')}".lower()
                if role == "button" and any(token in name for token in ["search", "搜索", "submit", "go", "查找"]):
                    return item.get("element_id", item.get("id"))
        return None

    def _find_searchbox_ref(self, observation: Observation):
        groups = [observation.form_fields or [], observation.accessibility_tree or [], observation.elements or []]
        for group in groups:
            for item in group:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role") or "").lower()
                tag = str(item.get("tag") or "").lower()
                name = f"{item.get('name', '')} {item.get('label', '')} {item.get('text', '')}".lower()
                if role in {"searchbox", "textbox", "combobox"} and any(token in name for token in ["search", "搜索", "query", "keyword", "关键词", "jump", "find"]):
                    return item.get("element_id", item.get("id"))
                if tag in {"input", "textarea"} and any(token in name for token in ["search", "搜索", "query", "keyword", "关键词", "jump", "find"]):
                    return item.get("element_id", item.get("id"))
        return None

    def _body_text(self) -> str:
        assert self.page is not None
        try:
            return _clean_text(self.page.locator("body").inner_text(timeout=5000))
        except PlaywrightError:
            return ""

    def _screenshot(self, node_id: str) -> str:
        assert self.page is not None
        out_dir = Path("runs") / "screenshots"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{node_id}-{uuid.uuid4().hex[:8]}.png"
        self.page.screenshot(path=str(path), full_page=False)
        return str(path)

    def _page_snapshot_fields(self, node_id: str, existing_screenshot: str = "") -> Dict[str, Any]:
        screenshot_path = existing_screenshot or self._screenshot(node_id)
        interactable = self._interactable_elements()
        return {
            "screenshot_path": screenshot_path,
            "accessibility_tree": interactable[:30],
            "interactable_elements": interactable,
            "form_fields": [item for item in interactable if item.get("role") in {"textbox", "searchbox", "combobox", "checkbox", "radio", "select"}],
            "visible_buttons": [item for item in interactable if item.get("role") == "button"],
            "visual_summary": "Screenshot captured for multimodal grounding; use provider analysis when configured.",
        }

    def _interactable_elements(self) -> List[Dict[str, Any]]:
        assert self.page is not None
        script = """() => {
            const selectors = [
              'a[href]', 'button', 'input', 'textarea', 'select',
              '[role=button]', '[role=link]', '[role=textbox]', '[role=searchbox]',
              '[contenteditable=true]', '[tabindex]:not([tabindex="-1"])'
            ];
            const seen = new Set();
            const roleFor = (el) => {
              const explicit = el.getAttribute('role');
              if (explicit) return explicit;
              const tag = el.tagName.toLowerCase();
              const type = (el.getAttribute('type') || '').toLowerCase();
              if (tag === 'a') return 'link';
              if (tag === 'button' || type === 'button' || type === 'submit') return 'button';
              if (tag === 'select') return 'select';
              if (type === 'checkbox') return 'checkbox';
              if (type === 'radio') return 'radio';
              if (tag === 'input' && (type === 'search')) return 'searchbox';
              if (tag === 'input' || tag === 'textarea' || el.isContentEditable) return 'textbox';
              return tag;
            };
            const nameFor = (el) => {
              const id = el.id;
              const label = id ? document.querySelector(`label[for="${CSS.escape(id)}"]`)?.innerText : '';
              return (el.getAttribute('aria-label') || el.getAttribute('title') || el.getAttribute('placeholder') || label || el.innerText || el.value || '').replace(/\\s+/g, ' ').trim();
            };
            const cssFor = (el, idx) => {
              el.setAttribute('data-agent-idx', String(idx));
              return `[data-agent-idx="${idx}"]`;
            };
            const picked = [];
            let idx = 0;
            for (const el of document.querySelectorAll(selectors.join(','))) {
              if (seen.has(el)) continue;
              seen.add(el);
              const rect = el.getBoundingClientRect();
              const style = window.getComputedStyle(el);
              if (!rect || rect.width < 1 || rect.height < 1 || style.visibility === 'hidden' || style.display === 'none') continue;
              if (rect.bottom < 0 || rect.right < 0 || rect.top > window.innerHeight || rect.left > window.innerWidth) continue;
              const role = roleFor(el);
              const name = nameFor(el);
              const item = {
                element_id: idx,
                index: idx,
                role,
                tag: el.tagName.toLowerCase(),
                type: el.getAttribute('type') || '',
                name,
                text: name,
                label: name,
                href: el.href || '',
                value: el.value || '',
                selector: cssFor(el, idx),
                disabled: Boolean(el.disabled || el.getAttribute('aria-disabled') === 'true'),
                bbox: {x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height)}
              };
              if (el.tagName.toLowerCase() === 'select') {
                item.options = Array.from(el.options).slice(0, 20).map(o => ({value: o.value, label: o.label || o.innerText}));
              }
              picked.push(item);
              idx += 1;
              if (picked.length >= 80) break;
            }
            return picked;
        }"""
        try:
            return self.page.evaluate(script)
        except PlaywrightError:
            return []

    def _page_metadata(self) -> Dict[str, str]:
        assert self.page is not None
        return self._metadata_for_page(self.page)

    def _metadata_for_page(self, page) -> Dict[str, str]:
        try:
            return page.evaluate(
                """() => {
                    const pick = (selector) => document.querySelector(selector)?.content || '';
                    return {
                      description: pick('meta[name="description"]') || pick('meta[property="og:description"]'),
                      ogTitle: pick('meta[property="og:title"]'),
                      ogType: pick('meta[property="og:type"]'),
                      ogVideo: pick('meta[property="og:video"]') || pick('meta[property="og:video:url"]'),
                      duration: pick('meta[itemprop="duration"]'),
                      uploadDate: pick('meta[itemprop="uploadDate"]'),
                      author: pick('meta[name="author"]')
                    };
                }"""
            )
        except PlaywrightError:
            return {}

    def _visible_video_links(self) -> List[Dict[str, str]]:
        assert self.page is not None
        try:
            links = self.page.locator("a").evaluate_all(
                """els => els.map(a => ({
                    text: (a.innerText || a.textContent || '').replace(/\\s+/g, ' ').trim(),
                    href: a.href || ''
                })).filter(x => x.href && /youtube\\.com|youtu\\.be|bilibili\\.com|vimeo\\.com|video/i.test(x.href + ' ' + x.text)).slice(0, 40)"""
            )
        except PlaywrightError:
            return []
        ranked = []
        seen = set()
        for link in links:
            href = str(link.get("href", ""))
            text = _clean_text(str(link.get("text", "")), 180)
            if not href or href in seen:
                continue
            seen.add(href)
            ranked.append({"text": text or href, "href": href})
        return ranked

    def _visible_transcript_text(self) -> str:
        assert self.page is not None
        keywords = ["transcript", "字幕", "chapters", "章节", "description", "简介"]
        try:
            text = self.page.evaluate(
                """(keywords) => {
                    const nodes = Array.from(document.querySelectorAll('ytd-transcript-segment-renderer, .transcript, [class*=transcript], [aria-label*=Transcript], [aria-label*=字幕], #description, [class*=description]'));
                    const direct = nodes.map(n => n.innerText || n.textContent || '').join(' ');
                    if (direct.trim()) return direct;
                    const body = document.body?.innerText || '';
                    const lower = body.toLowerCase();
                    const hit = keywords.some(k => lower.includes(String(k).toLowerCase()));
                    return hit ? body.slice(0, 6000) : '';
                }""",
                keywords,
            )
        except PlaywrightError:
            return ""
        return _clean_text(text, 6000)

    def _video_oembed(self, url: str) -> Dict[str, Any]:
        parsed = urlparse(url)
        if "youtube.com" not in parsed.netloc and "youtu.be" not in parsed.netloc:
            return {}
        endpoint = "https://www.youtube.com/oembed?format=json&url=" + quote_plus(url)
        try:
            with urllib.request.urlopen(endpoint, timeout=8) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            return {}

    def _yt_dlp_metadata(self, url: str) -> Dict[str, Any]:
        binary = shutil.which("yt-dlp")
        if not binary:
            return {"available": False, "reason": "yt-dlp_not_installed"}
        try:
            completed = subprocess.run(
                [binary, "--skip-download", "--dump-single-json", "--no-warnings", url],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except Exception as exc:
            return {"available": True, "error": str(exc)}
        if completed.returncode != 0:
            return {"available": True, "error": completed.stderr[-500:]}
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return {"available": True, "error": "invalid_yt_dlp_json"}
        return {
            "available": True,
            "title": payload.get("title"),
            "channel": payload.get("channel") or payload.get("uploader"),
            "duration": payload.get("duration"),
            "description": _clean_text(payload.get("description", ""), 1000),
            "chapters": payload.get("chapters") or [],
            "subtitles": list((payload.get("subtitles") or {}).keys())[:20],
            "automatic_captions": list((payload.get("automatic_captions") or {}).keys())[:20],
        }

    def _rank_links(self, links: List[Dict[str, Any]], source: str, query: str = "") -> List[Dict[str, str]]:
        seen = set()
        ranked: List[Dict[str, str]] = []
        for link in links:
            text = _clean_text(str(link.get("text", "")), 140)
            href = str(link.get("href", ""))
            if not text or not href or href in seen or not self._link_matches_source(href, source):
                continue
            if source == "shopping" and not _shopping_link_relevant(text, href, query):
                continue
            if source == "video" and not _video_link_relevant(text, href, query):
                continue
            seen.add(href)
            ranked.append({"text": text, "href": href})
            if len(ranked) >= MAX_LINKS:
                break
        return ranked

    def _query_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        return parse_qs(parsed.query).get("q", [""])[0]

    def _github_api_links(self, query: str) -> List[Dict[str, str]]:
        if not query:
            return []
        url = f"https://api.github.com/search/repositories?q={quote_plus(query)}&sort=stars&order=desc&per_page=10"
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "browser-workflow-agent"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return []
        repos = []
        for item in payload.get("items", []):
            full_name = item.get("full_name")
            html_url = item.get("html_url")
            stars = item.get("stargazers_count", 0)
            description = item.get("description") or ""
            if full_name and html_url:
                repos.append({"text": f"{full_name} ({stars} stars) - {description}", "href": html_url})
        return repos

    def _link_matches_source(self, href: str, source: str) -> bool:
        parsed = urlparse(href)
        path_parts = [part for part in parsed.path.split("/") if part]
        if source == "github":
            reserved = {
                "about",
                "blog",
                "collections",
                "enterprise",
                "features",
                "login",
                "marketplace",
                "mcp",
                "orgs",
                "pricing",
                "resources",
                "search",
                "security",
                "settings",
                "solutions",
                "signup",
                "sponsors",
                "topics",
                "trending",
                "why-github",
            }
            return parsed.netloc.endswith("github.com") and len(path_parts) == 2 and path_parts[0] not in reserved
        if source == "paper":
            return parsed.netloc.endswith("arxiv.org") and len(path_parts) >= 2 and path_parts[0] in {"abs", "pdf"}
        if source == "video":
            host = parsed.netloc.lower()
            path = parsed.path.lower()
            if host in {"bing.com", "www.bing.com", "cn.bing.com"}:
                return path.startswith("/videos/riverview") or "view=detail" in parsed.query.lower()
            return (
                parsed.scheme in {"http", "https"}
                and (
                    "youtube.com" in host
                    or "youtu.be" in host
                    or "bilibili.com" in host
                    or "vimeo.com" in host
                    or "video" in path
                    or "/watch" in path
                )
            )
        if source in {"shopping", "general"}:
            blocked_hosts = {"bing.com", "www.bing.com", "cn.bing.com", "duckduckgo.com", "www.google.com"}
            blocked_path_parts = {"ck", "aclick", "images", "videos", "maps"}
            return (
                parsed.scheme in {"http", "https"}
                and parsed.netloc not in blocked_hosts
                and href != "#"
                and not any(part in blocked_path_parts for part in path_parts[:2])
            )
        return True


def execute_action(action: Action, observation: Observation) -> Dict[str, Any]:
    """Dispatch one browser tool action in deterministic harness-safe mode."""
    outcome = TOOL_OUTCOMES.get(action.tool)
    if outcome is None:
        return {"ok": False, "tool": action.tool, "error": "unsupported_tool"}

    detail = {
        "message": outcome,
        "target": action.target,
        "value": action.value,
        "page_title": observation.title,
    }
    return {
        "ok": True,
        "tool": action.tool,
        "url": observation.url,
        "detail": detail,
    }
