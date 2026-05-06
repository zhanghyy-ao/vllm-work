from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .schema import Action, Observation


@dataclass
class AgentMemory:
    task: str
    search_queries: List[str] = field(default_factory=list)
    visited_urls: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    candidate_snapshots: List[Dict[str, Any]] = field(default_factory=list)
    detail_pages: List[Dict[str, Any]] = field(default_factory=list)

    def remember(self, action: Action, observation: Observation, output: Any = None, artifact: str = "") -> None:
        if observation.url and observation.url not in self.visited_urls:
            self.visited_urls.append(observation.url)

        if action.type == "type" and action.value:
            target = self._target(observation, action.target_id)
            if target and ("search" in target.haystack() or "搜索" in target.haystack()):
                query = str(action.value).strip()
                if query and query not in self.search_queries:
                    self.search_queries.append(query)
                    self.notes.append(f"记录搜索关键词：{query}")

        if action.type == "navigate" and action.value:
            self.notes.append(f"访问页面：{action.value}")

        if observation.cards:
            snapshot = {
                "url": observation.url,
                "title": observation.title,
                "cards": [dict(card) for card in observation.cards[:12]],
            }
            if snapshot not in self.candidate_snapshots:
                self.candidate_snapshots.append(snapshot)
                self.candidate_snapshots = self.candidate_snapshots[-6:]

        if action.type in {"extract", "summarize", "collect", "compare", "brief", "find"} and artifact:
            note = f"{action.type} 产出长度 {len(artifact)}"
            if note not in self.notes:
                self.notes.append(note)
                self.notes = self.notes[-16:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "searchQueries": self.search_queries,
            "visitedUrls": self.visited_urls,
            "notes": self.notes,
            "candidateSnapshots": self.candidate_snapshots,
            "detailPages": self.detail_pages,
        }

    def summary(self) -> str:
        parts = []
        if self.search_queries:
            parts.append("搜索关键词：" + " / ".join(self.search_queries[-3:]))
        if self.visited_urls:
            parts.append(f"访问页面数：{len(self.visited_urls)}")
        if self.candidate_snapshots:
            count = sum(len(snapshot.get("cards", [])) for snapshot in self.candidate_snapshots)
            parts.append(f"累计候选：{count}")
        if self.detail_pages:
            parts.append(f"详情页采样：{len(self.detail_pages)}")
        return "；".join(parts)

    def remember_detail_page(
        self,
        candidate: Dict[str, Any],
        observation: Observation,
        summary: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        metadata = metadata or {}
        title = str(candidate.get("title") or observation.title or "").strip()
        url = str(candidate.get("href") or observation.url or "").strip()
        headings = [heading for heading in observation.headings[:8] if not _is_boilerplate_line(heading)]
        capabilities = _clean_string_list(metadata.get("capabilities"), limit=6)
        install_steps = _clean_string_list(metadata.get("install"), limit=4)
        evidence = _clean_string_list(metadata.get("evidence"), limit=5)
        about = str(metadata.get("about") or "").strip()
        snapshot = {
            "candidateTitle": title,
            "url": url,
            "pageTitle": observation.title,
            "headings": headings,
            "about": about,
            "capabilities": capabilities,
            "install": install_steps,
            "evidence": evidence,
            "summary": summary or self._page_summary(observation, metadata),
        }
        existing = next((item for item in self.detail_pages if item.get("url") == url or item.get("candidateTitle") == title), None)
        if existing:
            existing.update(snapshot)
        else:
            self.detail_pages.append(snapshot)
            self.detail_pages = self.detail_pages[-8:]
        note = f"采样详情页：{title}"
        if note not in self.notes:
            self.notes.append(note)
            self.notes = self.notes[-16:]

    @staticmethod
    def _target(observation: Observation, target_id: str | None):
        if not target_id:
            return None
        return next((element for element in observation.elements if element.id == target_id), None)

    @staticmethod
    def _page_summary(observation: Observation, metadata: Optional[Dict[str, Any]] = None) -> str:
        metadata = metadata or {}
        snippets = []
        title_tagline = _extract_title_tagline(observation.title)
        if title_tagline:
            snippets.append(title_tagline)
        about = str(metadata.get("about") or "").strip()
        if about and not _is_boilerplate_line(about):
            snippets.append(about[:220])
        capabilities = _clean_string_list(metadata.get("capabilities"), limit=3)
        if capabilities:
            snippets.append("能力点：" + "；".join(capabilities))
        install_steps = _clean_string_list(metadata.get("install"), limit=2)
        if install_steps:
            snippets.append("安装线索：" + "；".join(install_steps))
        headings = [heading for heading in observation.headings if not _is_boilerplate_line(heading)]
        if headings:
            snippets.append("标题线索：" + " / ".join(headings[:3]))
        key_lines = _pick_semantic_lines(observation.text)
        if key_lines:
            snippets.append("内容摘要：" + "；".join(key_lines[:3]))
        return " | ".join(part for part in snippets if part) or observation.title


def _is_boilerplate_line(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return True
    patterns = [
        r"navigation menu",
        r"saved searches",
        r"provide feedback",
        r"skip to content",
        r"search code, repositories",
        r"toggle navigation",
        r"appearance settings",
        r"sign in",
        r"folders and files",
        r"latest commit",
        r"history",
        r"stars?",
        r"forks?",
        r"contributors?",
        r"github",
        r"jump to",
        r"branches",
        r"tags",
        r"report repository",
        r"notifications",
    ]
    return any(re.search(pattern, value, re.I) for pattern in patterns)


def _extract_title_tagline(title: str) -> str:
    value = str(title or "").strip()
    match = re.search(r":\s*(.+?)\s*[·|-]\s*GitHub$", value)
    if match:
        return match.group(1).strip()
    match = re.search(r":\s*(.+)$", value)
    return match.group(1).strip() if match else ""


def _clean_string_list(items: Any, limit: int = 6) -> List[str]:
    cleaned: List[str] = []
    if not isinstance(items, list):
        return cleaned
    for item in items:
        text = re.sub(r"\s+", " ", str(item or "")).strip(" -•\t")
        if not text or _is_boilerplate_line(text):
            continue
        if text not in cleaned:
            cleaned.append(text[:240])
        if len(cleaned) >= limit:
            break
    return cleaned


def _pick_semantic_lines(text: str, limit: int = 5) -> List[str]:
    preferred = []
    fallback = []
    keywords = re.compile(
        r"agent|browser|automation|workflow|playwright|chrome|llm|extension|助手|智能体|自动化|工作流|安装|配置|api|research|search|scrape",
        re.I,
    )
    for raw in re.split(r"[\n\r]+|(?<=[。！？])", str(text or "")):
        line = re.sub(r"\s+", " ", raw).strip(" -•\t")
        if len(line) < 18 or len(line) > 220 or _is_boilerplate_line(line):
            continue
        if keywords.search(line):
            if line not in preferred:
                preferred.append(line)
        elif len(fallback) < limit and line not in fallback:
            fallback.append(line)
        if len(preferred) >= limit:
            break
    return (preferred + fallback)[:limit]
