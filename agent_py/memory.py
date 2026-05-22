from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .schema import Action, Observation


@dataclass
class AgentMemory:
    """Shared memory across rounds/branches for search, sampling, and recommendation context."""
    task: str
    search_queries: List[str] = field(default_factory=list)
    visited_urls: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    candidate_snapshots: List[Dict[str, Any]] = field(default_factory=list)
    detail_pages: List[Dict[str, Any]] = field(default_factory=list)
    task_queue: List[Dict[str, Any]] = field(default_factory=list)
    workers: List[Dict[str, Any]] = field(default_factory=list)
    candidate_pool: List[Dict[str, Any]] = field(default_factory=list)
    evidence_by_candidate: Dict[str, List[str]] = field(default_factory=dict)
    source_graph: List[Dict[str, Any]] = field(default_factory=list)
    merge_log: List[Dict[str, Any]] = field(default_factory=list)
    open_branches: List[Dict[str, Any]] = field(default_factory=list)
    closed_branches: List[Dict[str, Any]] = field(default_factory=list)

    def remember(self, action: Action, observation: Observation, output: Any = None, artifact: str = "") -> None:
        """Append lightweight behavioral memory after each action execution."""
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
            "taskQueue": self.task_queue,
            "workers": self.workers,
            "candidatePool": self.candidate_pool,
            "evidenceByCandidate": self.evidence_by_candidate,
            "sourceGraph": self.source_graph,
            "mergeLog": self.merge_log,
            "openBranches": self.open_branches,
            "closedBranches": self.closed_branches,
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
        if self.workers:
            active = sum(1 for worker in self.workers if str(worker.get("status") or "") in {"pending", "active", "running"})
            parts.append(f"并行 worker：{active}/{len(self.workers)}")
        return "；".join(parts)

    def remember_workflow(self, task_queue: List[Dict[str, Any]], workers: List[Dict[str, Any]], branches: List[Dict[str, Any]]) -> None:
        self.task_queue = [dict(item) for item in task_queue]
        self.workers = [dict(item) for item in workers]
        self.open_branches = [dict(item) for item in branches]
        note = f"更新阶段队列：{len(task_queue)} 个任务，{len(branches)} 个并行分支"
        if note not in self.notes:
            self.notes.append(note)
            self.notes = self.notes[-20:]

    def merge_branch_result(self, branch_result: Dict[str, Any]) -> None:
        """Merge parallel branch outputs into global candidate/evidence pools."""
        branch_id = str(branch_result.get("branchId") or branch_result.get("branch_id") or "")
        worker_id = str(branch_result.get("workerId") or branch_result.get("worker_id") or "")
        data = branch_result.get("data") if isinstance(branch_result.get("data"), dict) else {}
        summary = str(branch_result.get("summary") or "").strip()
        target_url = str(branch_result.get("targetUrl") or branch_result.get("target_url") or "")

        cards = data.get("cards") if isinstance(data.get("cards"), list) else []
        for card in cards:
            if not isinstance(card, dict):
                continue
            title = str(card.get("title") or "").strip()
            if not title:
                continue
            existing = next((item for item in self.candidate_pool if item.get("title") == title), None)
            merged = {
                "title": title,
                "summary": str(card.get("summary") or "")[:240],
                "href": str(card.get("href") or target_url),
                "workerId": worker_id,
                "branchId": branch_id,
            }
            if existing:
                for key, value in merged.items():
                    if value and not existing.get(key):
                        existing[key] = value
            else:
                self.candidate_pool.append(merged)
        if summary:
            key = branch_id or target_url or worker_id or f"branch-{len(self.merge_log) + 1}"
            self.source_graph.append({"branchId": branch_id, "workerId": worker_id, "targetUrl": target_url, "summary": summary})
            self.evidence_by_candidate.setdefault(key, [])
            if summary not in self.evidence_by_candidate[key]:
                self.evidence_by_candidate[key].append(summary)
        self.merge_log.append(
            {
                "branchId": branch_id,
                "workerId": worker_id,
                "targetUrl": target_url,
                "mergedKeys": sorted(list(data.keys())),
                "summary": summary[:160],
            }
        )
        self.merge_log = self.merge_log[-20:]
        if branch_id:
            self.closed_branches.append({"branchId": branch_id, "workerId": worker_id, "targetUrl": target_url, "summary": summary[:120]})
            self.closed_branches = self.closed_branches[-12:]
            self.open_branches = [item for item in self.open_branches if str(item.get("taskId") or item.get("task_id") or "") != branch_id]

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
