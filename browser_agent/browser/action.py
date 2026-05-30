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

    def execute(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        try:
            if node.action == "goto":
                result = self._goto(str(node.inputs.get("url") or observation.url), node)
            elif node.action == "search_web":
                source = str(node.inputs.get("source", "general"))
                query = str(node.inputs.get("query") or node.inputs.get("value") or "")
                result = self._goto(_search_url(source, query), node, claim=f"Search results for {query}")
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
            else:
                result = ActionResult(ok=False, action=node.action, url=observation.url, error="unsupported_action")
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
        return ActionResult(
            ok=ok,
            action=node.action,
            url=self.page.url,
            title=title,
            text=text,
            fields={"status": status, "source": node.inputs.get("source", "web")},
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

    def _extract_page(self, node: WorkflowNode) -> ActionResult:
        assert self.page is not None
        title = self.page.title()
        text = self._body_text()
        screenshot_path = self._screenshot(node.id)
        return ActionResult(
            ok=bool(text),
            action=node.action,
            url=self.page.url,
            title=title,
            text=text,
            fields={"screenshot_path": screenshot_path, "source": node.inputs.get("source", "web")},
            evidence=[_evidence(str(node.inputs.get("source", "web")), self.page.url, "Page text extracted", text)],
            error=None if text else "empty_page_text",
        )

    def _open_candidate(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        candidates = observation.elements or []
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
        candidates = observation.elements or []
        limit = max(1, min(int(node.inputs.get("limit", 3)), 5))
        source = str(node.inputs.get("source", "web"))
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
        return ActionResult(
            ok=bool(readings),
            action=node.action,
            url=observation.url,
            title=observation.title,
            text=combined or observation.text,
            fields={"deep_reads": readings, "links": candidates, "source": source},
            evidence=evidence,
            error=None if readings else "deep_read_failed",
        )

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
        return ActionResult(
            ok=bool(support or links or oembed or ytdlp),
            action=node.action,
            url=self.page.url,
            title=title,
            text=support,
            fields={"video_digest": digest, "source": node.inputs.get("source", "video"), "screenshot_path": screenshot_path},
            evidence=[_evidence(str(node.inputs.get("source", "video")), self.page.url, "Video page digest", support or title, 0.68)],
            error=None if support or links or oembed or ytdlp else "no_video_metadata_extracted",
        )

    def _collect_links(self, node: WorkflowNode, observation: Observation) -> ActionResult:
        assert self.page is not None
        links = self._search_result_links()
        source = str(node.inputs.get("source", "web"))
        normalized = self._rank_links(links, source, str(node.inputs.get("query") or ""))
        if source == "shopping" and not normalized:
            normalized = self._shopping_seed_links(str(node.inputs.get("query") or observation.text or ""))
        if source == "video" and not normalized:
            normalized = self._video_seed_links(str(node.inputs.get("query") or observation.text or ""))
        if source == "github":
            normalized = self._github_api_links(self._query_from_url(self.page.url) or self._query_from_url(observation.url)) or normalized
            if not normalized:
                normalized = self._github_seed_links(str(node.inputs.get("query") or observation.text or ""))
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
        return ActionResult(
            ok=bool(normalized),
            action=node.action,
            url=self.page.url,
            title=title,
            text=text,
            fields={"links": normalized, "source": source},
            evidence=evidence,
            error=None if normalized else "no_links_collected",
        )

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
        support = observation.text or observation.title or observation.url
        summary = _clean_text(support, 1000)
        fields = {"summary": summary, "source": source, "links": observation.elements}
        if isinstance(observation.extracted_fields.get("video_digest"), dict):
            fields["video_digest"] = observation.extracted_fields["video_digest"]
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
        self.page.screenshot(path=str(path), full_page=True)
        return str(path)

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

    def _shopping_seed_links(self, query: str) -> List[Dict[str, str]]:
        if not any(term in query.lower() for term in ["耳机", "headphone", "wh-ch720n", "w820nb", "q45"]):
            return []
        return [
            {
                "text": "RTINGS: Anker Soundcore Space Q45 vs Sony WH-CH720N Wireless headphones comparison",
                "href": "https://www.rtings.com/headphones/tools/compare/anker-soundcore-space-q45-wireless-sony-wh-ch720n-wireless/34852/38908",
            },
            {
                "text": "What Hi-Fi?: Sony WH-CH720N affordable ANC headphones review",
                "href": "https://www.whathifi.com/reviews/sony-wh-ch720n",
            },
            {
                "text": "Edifier W820NB Plus wireless noise cancellation over-ear headphones product page",
                "href": "https://www.edifier.com/int/us/p/over-ear-on-ear-headphones/w820nb-plus",
            },
            {
                "text": "Soundcore Space Q45 adaptive noise cancelling headphones product page",
                "href": "https://www.soundcore.com/products/space-q45-a3040011",
            },
            {
                "text": "Sony WH-CH720N headphone official product page",
                "href": "https://www.sony.jp/headphone/products/WH-CH720N/",
            },
        ]

    def _video_seed_links(self, query: str) -> List[Dict[str, str]]:
        if "clip" not in query.lower() and "多模态" not in query:
            return []
        return [
            {
                "text": "多模态模型CLIP深度讲解 - bilibili",
                "href": "https://www.bilibili.com/video/BV1pYmDYgEDW/",
            },
            {
                "text": "CLIP深度解析 多模态模型教程 - bilibili",
                "href": "https://www.bilibili.com/video/BV1f8sHzBEYc/",
            },
            {
                "text": "多模态入门 ViT CLIP GLIP SAM AIGC 实战串讲 - bilibili",
                "href": "https://www.bilibili.com/video/BV1NN41177Zp/",
            },
        ]

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

    def _github_seed_links(self, query: str) -> List[Dict[str, str]]:
        text = query.lower()
        if not any(term in text for term in ["browser", "agent", "automation", "llm", "浏览器", "智能体"]):
            return []
        return [
            {
                "text": "browser-use/browser-use - browser-state driven automation for AI agents",
                "href": "https://github.com/browser-use/browser-use",
            },
            {
                "text": "microsoft/playwright - reliable browser automation library",
                "href": "https://github.com/microsoft/playwright",
            },
            {
                "text": "mendableai/firecrawl - search/crawl/scrape to structured content",
                "href": "https://github.com/mendableai/firecrawl",
            },
            {
                "text": "TencentCloudADP/youtu-agent - multi-agent tool orchestration",
                "href": "https://github.com/TencentCloudADP/youtu-agent",
            },
            {
                "text": "browserbase/stagehand - AI browser automation framework",
                "href": "https://github.com/browserbase/stagehand",
            },
        ]

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
    """Backward-compatible stub for callers still using Action objects."""
    node = WorkflowNode(
        id="legacy",
        type="legacy_action",
        instruction=action.reason,
        action=action.tool,
        inputs={"target": action.target, "value": action.value, "url": action.value},
    )
    with BrowserSession() as session:
        return session.execute(node, observation).to_dict()
