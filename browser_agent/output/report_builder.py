from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urlparse

from browser_agent.failure_policy import summarize_failure_types
from browser_agent.strategy.research_patterns import requirement_slots
from browser_agent.types import EvidenceItem, StructuredArtifact, WorkflowSpec


def build_report(workflow: WorkflowSpec, memory_dump: Dict[str, Any], steps: List[Dict[str, Any]]) -> StructuredArtifact:
    evidence = [EvidenceItem(**item) for item in memory_dump.get("evidence", [])]
    candidates = _candidate_rows(evidence)
    source_readings = _source_readings(steps)
    requirement_progression = _workflow_requirement_progression(workflow, steps)
    report_status = _report_status(steps, requirement_progression, candidates)
    comparison_matrix = _scored_comparison_matrix(_basic_comparison_matrix(candidates, workflow.domain, source_readings), workflow.domain)
    recommendations = _recommendations(workflow.domain, candidates, comparison_matrix)
    uncertainties = _uncertainties(steps, candidates, requirement_progression, report_status)
    return StructuredArtifact(
        summary=_summary(workflow, candidates, evidence, requirement_progression, report_status),
        candidates=candidates,
        source_readings=source_readings,
        recommendations=recommendations,
        reasoning_outline=_workflow_reasoning_outline(workflow),
        subquestions=_workflow_subquestions(workflow),
        requirement_progression=requirement_progression,
        evidence_plan=_workflow_evidence_plan(workflow),
        search_plan=_workflow_search_plan(workflow),
        decision_criteria=_workflow_decision_criteria(workflow),
        comparison_matrix=comparison_matrix,
        video_digest=_video_digest(steps),
        multimodal_notes=_multimodal_notes(workflow, steps),
        failure_analysis=_failure_analysis(steps),
        uncertainties=uncertainties,
        next_actions=_next_actions(workflow.domain, report_status, requirement_progression, bool(candidates)),
        citations=[
            {
                "source_url": item.source_url,
                "claim": item.claim,
                "confidence": item.confidence,
            }
            for item in evidence[:15]
        ],
    )


def _source_readings(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    readings: List[Dict[str, Any]] = []
    seen = set()
    for step in steps:
        detail = step.get("detail", {})
        fields = detail.get("fields", {}) if isinstance(detail, dict) else {}
        for item in fields.get("deep_reads", []) if isinstance(fields.get("deep_reads"), list) else []:
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            if not url or url in seen:
                continue
            if _low_quality_url(url, " ".join(str(item.get(key, "")) for key in ["title", "description", "text", "name"])):
                continue
            seen.add(url)
            readings.append(item)
    return readings[:10]


def _video_digest(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    for step in reversed(steps):
        detail = step.get("detail", {})
        fields = detail.get("fields", {}) if isinstance(detail, dict) else {}
        digest = fields.get("video_digest")
        if isinstance(digest, dict) and digest:
            return digest
    return {}


def _multimodal_notes(workflow: WorkflowSpec, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    notes: List[Dict[str, Any]] = []
    digest = _video_digest(steps)
    screenshot_path = digest.get("screenshot_path")
    if workflow.domain == "video":
        notes.append(
            {
                "provider": "gemini",
                "status": "planned",
                "input": screenshot_path or "video key frames",
                "purpose": "Use Gemini vision to read visual scenes, slides, UI demonstrations, or key frames after frame extraction is enabled.",
            }
        )
    elif screenshot_path:
        notes.append(
            {
                "provider": "gemini",
                "status": "available_for_follow_up",
                "input": screenshot_path,
                "purpose": "Screenshot can be passed to Gemini for visual grounding.",
            }
        )
    return notes


def _workflow_decision_criteria(workflow: WorkflowSpec) -> List[Dict[str, Any]]:
    for node in workflow.nodes:
        criteria = node.inputs.get("decision_criteria")
        if isinstance(criteria, list) and criteria:
            return [item for item in criteria if isinstance(item, dict)][:8]
    if workflow.domain == "shopping":
        return [
            {"name": "价格", "why_it_matters": "控制预算并比较性价比", "evidence_to_collect": "价格区间、促销和保修"},
            {"name": "类型", "why_it_matters": "入耳式、头戴式、开放式适合不同场景", "evidence_to_collect": "佩戴形态和使用场景"},
            {"name": "核心体验", "why_it_matters": "音质、降噪、舒适度决定长期满意度", "evidence_to_collect": "评测结论和用户反馈"},
        ]
    return []


def _workflow_reasoning_outline(workflow: WorkflowSpec) -> List[str]:
    for node in workflow.nodes:
        outline = node.inputs.get("reasoning_outline")
        if isinstance(outline, list) and outline:
            return [str(item) for item in outline if str(item).strip()][:8]
    if workflow.domain == "shopping":
        return [
            "先把推荐问题拆成预算、使用场景、候选型号、核心体验和风险点几个需求槽位。",
            "先观察当前页面是否已有可点击候选、搜索框或筛选控件，再决定是否需要离开当前页。",
            "进入候选页面后优先抽取价格、专业评测、用户反馈和明显短板，持续补齐缺口。",
            "最终按当前页面收集到的证据强弱给出推荐，而不是按关键词命中顺序排序。",
        ]
    return ["先拆解任务目标和证据需求，再根据当前页面状态决定是页内推进、打开候选，还是补一次外部检索。"]


def _workflow_subquestions(workflow: WorkflowSpec) -> List[str]:
    for node in workflow.nodes:
        subquestions = node.inputs.get("subquestions")
        if isinstance(subquestions, list) and subquestions:
            return [str(item) for item in subquestions if str(item).strip()][:10]
    if workflow.domain == "shopping":
        return [
            "预算内有哪些主流品牌和型号反复出现在评测/榜单中？",
            "这些型号分别属于什么类型，是否适合通勤和办公室？",
            "价格、音质、降噪、舒适度和用户评价有哪些可验证线索？",
            "每个候选的主要短板和购买风险是什么？",
        ]
    return []


def _workflow_search_plan(workflow: WorkflowSpec) -> List[Dict[str, Any]]:
    return _workflow_evidence_plan(workflow)


def _workflow_evidence_plan(workflow: WorkflowSpec) -> List[Dict[str, Any]]:
    plan: List[Dict[str, Any]] = []
    slot_index = {str(item.get("slot")): item for item in requirement_slots(workflow.domain, workflow.goal)}
    for node in workflow.nodes:
        slot = str(node.inputs.get("requirement_slot") or node.inputs.get("evidence_stage") or "")
        if node.action != "search_web" and not slot:
            continue
        slot_meta = slot_index.get(slot, {})
        plan.append(
            {
                "evidence_hint": node.inputs.get("query"),
                "query": node.inputs.get("query"),
                "purpose": node.inputs.get("llm_purpose") or slot_meta.get("purpose") or node.instruction,
                "source": node.inputs.get("source") or slot_meta.get("source"),
                "evidence_stage": node.inputs.get("evidence_stage"),
                "requirement_slot": slot,
            }
        )
    if plan:
        return plan[:8]
    return [
        {
            "evidence_hint": "",
            "query": "",
            "purpose": item.get("purpose"),
            "source": item.get("source"),
            "evidence_stage": item.get("slot"),
            "requirement_slot": item.get("slot"),
        }
        for item in requirement_slots(workflow.domain, workflow.goal)[:8]
    ]


def _workflow_requirement_progression(workflow: WorkflowSpec, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    slot_index = {
        str(item.get("slot")): {
            "requirement_slot": item.get("slot"),
            "purpose": item.get("purpose"),
            "source": item.get("source"),
            "status": "missing",
            "latest_action": "",
            "latest_url": "",
            "evidence_summary": "",
        }
        for item in requirement_slots(workflow.domain, workflow.goal)
        if item.get("slot")
    }
    for step in steps:
        detail = step.get("detail", {}) if isinstance(step, dict) else {}
        fields = detail.get("fields", {}) if isinstance(detail, dict) else {}
        slot = str(fields.get("requirement_slot") or fields.get("evidence_stage") or "")
        if not slot:
            continue
        entry = slot_index.setdefault(
            slot,
            {
                "requirement_slot": slot,
                "purpose": step.get("action") or "unknown",
                "source": fields.get("source") or "",
                "status": "missing",
                "latest_action": "",
                "latest_url": "",
                "evidence_summary": "",
            },
        )
        entry["latest_action"] = step.get("action") or entry.get("latest_action") or ""
        entry["latest_url"] = detail.get("url") or entry.get("latest_url") or ""
        entry["source"] = fields.get("source") or entry.get("source") or ""
        entry["status"] = "satisfied" if step.get("ok") else "partial"
        entry["evidence_summary"] = _slot_evidence_summary(fields, detail)
    ordered = list(slot_index.values())
    ordered.sort(key=lambda item: (0 if item.get("status") == "satisfied" else 1 if item.get("status") == "partial" else 2))
    return ordered[:8]


def _slot_evidence_summary(fields: Dict[str, Any], detail: Dict[str, Any]) -> str:
    for key in [
        "repo_metadata_signals",
        "implementation_doc_signals",
        "review_signals",
        "comparison_signals",
        "marketplace_signals",
        "comment_signals",
        "transcript_signals",
        "visual_signals",
        "candidate_pool_signals",
        "repo_candidate_signals",
        "video_candidate_signals",
        "requirement_slot_signals",
    ]:
        payload = fields.get(key)
        if isinstance(payload, dict) and payload.get("summary"):
            return str(payload.get("summary"))
    if isinstance(fields.get("summary"), str) and fields.get("summary"):
        return str(fields.get("summary"))
    if isinstance(detail.get("text"), str) and detail.get("text"):
        return str(detail.get("text"))[:180]
    if isinstance(fields.get("links"), list) and fields.get("links"):
        return f"collected {len(fields['links'])} visible candidates"
    return ""


def _basic_comparison_matrix(
    candidates: List[Dict[str, Any]],
    domain: str,
    source_readings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if source_readings:
        return [_reading_to_matrix_row(item, domain) for item in source_readings[:6]]
    if not candidates:
        return []
    rows: List[Dict[str, Any]] = []
    for candidate in candidates[:6]:
        row = {
            "name": candidate.get("name"),
            "url": candidate.get("url"),
            "evidence_strength": candidate.get("confidence"),
        }
        if domain == "shopping":
            row.update(
                {
                    "price_signal": "needs_deeper_page_extraction",
                    "review_signal": candidate.get("support", "")[:160],
                    "fit_notes": "compare against budget, usage scenario, comfort, ANC, and warranty",
                }
            )
        rows.append(row)
    return rows


def _scored_comparison_matrix(rows: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
    scored = []
    for row in rows:
        score, reasons = _score_row(row, domain)
        scored.append({**row, "score": score, "score_reasons": reasons})
    return sorted(scored, key=lambda item: item.get("score", 0), reverse=True)


def _score_row(row: Dict[str, Any], domain: str) -> tuple[float, List[str]]:
    score = float(row.get("evidence_strength") or 0.0) * 20
    reasons: List[str] = []
    text = " ".join(str(row.get(key, "")) for key in ["name", "title", "description", "snippet", "review_signal", "readme_signal"]).lower()
    if domain == "github":
        stars = _safe_number(row.get("stars"))
        forks = _safe_number(row.get("forks"))
        topics = row.get("topics") if isinstance(row.get("topics"), list) else []
        if stars:
            score += min(30, _logish(stars) * 5)
            reasons.append(f"{int(stars)} stars")
        if forks:
            score += min(10, _logish(forks) * 2)
        if row.get("language"):
            score += 8
            reasons.append(f"language={row.get('language')}")
        if row.get("license"):
            score += 6
            reasons.append(f"license={row.get('license')}")
        if topics:
            score += min(8, len(topics))
            reasons.append("topics matched")
        if row.get("readme_signal"):
            score += 10
            reasons.append("README available")
        if row.get("updated_at"):
            score += 8
            reasons.append("recent metadata available")
    elif domain == "shopping":
        if row.get("price_signal") and row.get("price_signal") != "not_found":
            score += 18
            reasons.append(f"price={row.get('price_signal')}")
        if any(term in text for term in ["review", "评测", "tested", "verdict"]):
            score += 18
            reasons.append("review evidence")
        if any(term in text for term in ["noise", "anc", "降噪"]):
            score += 12
            reasons.append("ANC/noise evidence")
        if any(term in text for term in ["comfort", "comfortable", "舒适"]):
            score += 8
            reasons.append("comfort evidence")
        if any(term in text for term in ["compare", "comparison", "对比"]):
            score += 8
            reasons.append("comparison evidence")
    elif domain == "video":
        if any(term in text for term in ["clip", "多模态", "multimodal"]):
            score += 22
            reasons.append("topic match")
        if any(term in text for term in ["教程", "tutorial", "入门", "讲解"]):
            score += 18
            reasons.append("tutorial fit")
        if any(term in text for term in ["字幕", "transcript", "chapter", "章节"]):
            score += 8
            reasons.append("text/segment signal")
    else:
        if row.get("snippet") or row.get("description"):
            score += 10
            reasons.append("content evidence")
    return round(score, 2), reasons or ["ranked by collected evidence strength"]


def _safe_number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _logish(value: float) -> float:
    current = max(0.0, value)
    buckets = 0.0
    while current >= 10:
        buckets += 1
        current /= 10
    return buckets + min(current / 10, 1)


def _reading_to_matrix_row(reading: Dict[str, Any], domain: str) -> Dict[str, Any]:
    row = {
        "name": reading.get("name") or reading.get("title"),
        "url": reading.get("url"),
        "evidence_strength": 0.78 if reading.get("ok") else 0.45,
        "title": reading.get("title"),
        "description": reading.get("description"),
        "source_status": reading.get("status"),
        "snippet": str(reading.get("text", ""))[:220],
    }
    if domain == "shopping":
        row.update(
            {
                "price_signal": reading.get("price_signal") or "not_found",
                "review_signal": str(reading.get("text", ""))[:180],
                "fit_notes": "derived_from_deep_candidate_page",
            }
        )
    if domain == "github":
        repo = reading.get("repo") if isinstance(reading.get("repo"), dict) else {}
        parsed_stars = _parse_star_count(" ".join(str(reading.get(key, "")) for key in ["name", "title", "description", "text"]))
        row.update(
            {
                "stars": repo.get("stars") if repo else parsed_stars,
                "forks": repo.get("forks"),
                "language": repo.get("language"),
                "license": repo.get("license"),
                "updated_at": repo.get("updated_at"),
                "topics": repo.get("topics", []),
                "readme_signal": str(repo.get("readme_excerpt", ""))[:180],
                "fit_notes": "derived_from_github_api_and_readme" if repo else "derived_from_github_page_or_search_snippet",
            }
        )
    return row


def _parse_star_count(text: str) -> int | None:
    import re

    match = re.search(r"([\d,.]+)\s+stars?", text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return int(float(match.group(1).replace(",", "")))
    except ValueError:
        return None


def _report_status(
    steps: List[Dict[str, Any]],
    requirement_progression: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
) -> str:
    if not steps:
        return "unresolved"
    if any(not step.get("ok") for step in steps):
        return "needs_review"
    if not requirement_progression:
        return "completed" if candidates else "needs_review"
    statuses = [str(item.get("status") or "missing") for item in requirement_progression]
    if statuses and all(status == "satisfied" for status in statuses):
        return "completed"
    if any(status in {"satisfied", "partial"} for status in statuses):
        return "partial"
    return "needs_review"


def _summary(
    workflow: WorkflowSpec,
    candidates: List[Dict[str, Any]],
    evidence: List[EvidenceItem],
    requirement_progression: List[Dict[str, Any]],
    report_status: str,
) -> str:
    satisfied = sum(1 for item in requirement_progression if item.get("status") == "satisfied")
    partial = sum(1 for item in requirement_progression if item.get("status") == "partial")
    total = len(requirement_progression)
    if report_status == "completed":
        return (
            f"Workflow '{workflow.template}' completed for '{workflow.goal}'. "
            f"The agent advanced from the current page state, satisfied {satisfied}/{total or satisfied} requirement slots, "
            f"collected {len(candidates)} candidate links, and accumulated {len(evidence)} evidence items."
        )
    if report_status == "partial":
        return (
            f"Workflow '{workflow.template}' made partial progress for '{workflow.goal}', "
            f"but requirement coverage is still incomplete ({satisfied} satisfied, {partial} partial, {max(total - satisfied - partial, 0)} missing). "
            f"Collected {len(candidates)} candidate links and {len(evidence)} evidence items so far."
        )
    return (
        f"Workflow '{workflow.template}' did not yet reach a reliable result for '{workflow.goal}'. "
        f"The current page state and collected evidence are still insufficient for completion. "
        f"Collected {len(candidates)} candidate links and {len(evidence)} evidence items."
    )


def _candidate_rows(evidence: List[EvidenceItem]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen = set()
    for item in evidence:
        if not item.claim.startswith("Candidate link:"):
            continue
        if item.source_url == "about:blank":
            continue
        if not item.source_url or item.source_url in seen:
            continue
        if _low_quality_url(item.source_url, item.claim):
            continue
        seen.add(item.source_url)
        rows.append(
            {
                "name": item.claim.replace("Candidate link: ", "")[:120],
                "url": item.source_url,
                "support": item.support,
                "confidence": item.confidence,
            }
        )
        if len(rows) >= 10:
            break
    return rows


def _recommendations(domain: str, candidates: List[Dict[str, Any]], comparison_matrix: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    label = {
        "github": "Prioritize repositories with active docs, recent commits, and clear training entrypoints.",
        "paper": "Prioritize papers with public PDFs, code links, and explicit evaluation settings.",
        "shopping": "Prioritize products with repeated review evidence and clear specs.",
        "video": "Prioritize videos with complete titles, descriptions, and learning sequence fit.",
    }.get(domain, "Prioritize candidates with stronger source evidence.")
    filtered_matrix = [
        item for item in comparison_matrix
        if item.get("url") and not _low_quality_url(str(item.get("url") or ""), " ".join(str(item.get(key, "")) for key in ["name", "title", "description", "snippet", "review_signal"]))
    ]
    filtered_candidates = [
        item for item in candidates
        if item.get("url") and not _low_quality_url(str(item.get("url") or ""), " ".join(str(item.get(key, "")) for key in ["name", "support"]))
    ]
    if filtered_matrix:
        return [
            {
                "rank": idx + 1,
                "name": item.get("name") or item.get("title"),
                "url": item.get("url"),
                "score": item.get("score"),
                "reason": f"{label} Evidence score {item.get('score')}: {', '.join(item.get('score_reasons', []))}",
            }
            for idx, item in enumerate(filtered_matrix[:5])
            if item.get("url")
        ]
    return [
        {
            "rank": idx + 1,
            "name": candidate["name"],
            "url": candidate["url"],
            "reason": label,
        }
        for idx, candidate in enumerate(filtered_candidates[:5])
    ]


def _low_quality_url(url: str, text: str = "") -> bool:
    if not url:
        return True
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    haystack = f"{url} {text}".lower()
    blocked_hosts = {
        "gitcode.csdn.net",
        "devpress.csdn.net",
        "blog.csdn.net",
        "atomgit.com",
    }
    if host in blocked_hosts or host.endswith(".csdn.net"):
        return True
    blocked_terms = ["开源社区", "代码托管", "仓库镜像", "mirror", "转载", "登录后", "验证码", "403", "forbidden", "access denied", "gitcode", "atomgit", "csdn"]
    return any(term.lower() in haystack for term in blocked_terms)


def _uncertainties(
    steps: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    requirement_progression: List[Dict[str, Any]],
    report_status: str,
) -> List[str]:
    uncertainties: List[str] = []
    failed = [step for step in steps if not step.get("ok")]
    if failed:
        uncertainties.append("Some workflow steps failed or required fallback; inspect the recent page state and retry path before trusting the result.")
        failure_counts = summarize_failure_types(steps).get("failure_type_counts", {})
        if failure_counts.get("recognition_failure"):
            uncertainties.append("Recognition failures occurred: the current page structure was insufficient or ambiguous for stable extraction.")
        if failure_counts.get("planning_failure"):
            uncertainties.append("Planning failures occurred: the planner could not consistently map the current page state to a valid next action.")
        if failure_counts.get("execution_failure"):
            uncertainties.append("Execution failures occurred: the chosen browser action or the page response failed after planning.")
    partial_slots = [str(item.get("requirement_slot") or "") for item in requirement_progression if item.get("status") == "partial"]
    missing_slots = [str(item.get("requirement_slot") or "") for item in requirement_progression if item.get("status") == "missing"]
    if report_status != "completed" and partial_slots:
        uncertainties.append(f"Requirement coverage is still partial on: {', '.join(partial_slots[:4])}.")
    if report_status != "completed" and missing_slots:
        uncertainties.append(f"Requirement coverage is still missing on: {', '.join(missing_slots[:4])}.")
    if not candidates:
        uncertainties.append("Candidate extraction is still incomplete; the current page likely needs one more in-page recovery step or a carefully chosen fallback source.")
    return uncertainties or ["This MVP still mixes rule-based extraction with agent planning, so the final ranking should be manually spot-checked."]


def _failure_analysis(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary = summarize_failure_types(steps)
    counts = summary.get("failure_type_counts", {})
    failed_steps = [step for step in steps if not step.get("ok")]
    latest_examples = {}
    for step in failed_steps:
        failure_type = str(step.get("failure_type") or "")
        if failure_type and failure_type not in latest_examples:
            detail = step.get("detail", {}) if isinstance(step.get("detail"), dict) else {}
            latest_examples[failure_type] = {
                "action": step.get("action"),
                "error": detail.get("error") or step.get("reason") or "",
            }
    rows: List[Dict[str, Any]] = []
    for failure_type in ["recognition_failure", "planning_failure", "execution_failure"]:
        rows.append(
            {
                "failure_type": failure_type,
                "count": counts.get(failure_type, 0),
                "latest_example": latest_examples.get(failure_type, {}),
            }
        )
    return rows


def _next_actions(
    domain: str,
    report_status: str,
    requirement_progression: List[Dict[str, Any]],
    has_candidates: bool,
) -> List[str]:
    if report_status == "completed":
        return []
    partial_slots = [str(item.get("requirement_slot") or "") for item in requirement_progression if item.get("status") == "partial"]
    missing_slots = [str(item.get("requirement_slot") or "") for item in requirement_progression if item.get("status") == "missing"]
    if partial_slots:
        return [
            f"Continue from the current page and strengthen evidence for: {', '.join(partial_slots[:3])}.",
            "Prefer current-page interactables and deeper page reads before issuing a new external query.",
        ]
    if missing_slots and has_candidates:
        return [
            f"Collect the remaining requirement slots: {', '.join(missing_slots[:3])}.",
            "Keep the harness page-first: open visible candidates and extract missing evidence before broadening search.",
        ]
    if not has_candidates:
        if domain == "github":
            return ["Prefer opening repository candidates already visible on the current page; only then fall back to GitHub metadata retrieval."]
        if domain == "paper":
            return ["Prefer opening paper candidates already visible on the current page, then fall back to arXiv retrieval only if the page offers no stable path."]
        if domain == "video":
            return ["Prefer opening a visible video candidate from the current page, then extract transcript, description, and screenshot evidence."]
        return ["Continue with in-page search-box recovery, candidate extraction, and only then a source-specific fallback before asking for human review."]
    if domain == "github":
        return ["Open the top visible repositories, inspect README/code entrypoints, then verify recent activity."]
    if domain == "paper":
        return ["Open the most relevant visible papers, extract method/dataset/metric fields, then cross-check code availability."]
    return ["Review the top visible candidates and run a deeper extraction workflow on the best matches."]
