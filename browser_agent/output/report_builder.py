from __future__ import annotations

from typing import Any, Dict, List

from browser_agent.types import EvidenceItem, StructuredArtifact, WorkflowSpec


def build_report(workflow: WorkflowSpec, memory_dump: Dict[str, Any], steps: List[Dict[str, Any]]) -> StructuredArtifact:
    evidence = [EvidenceItem(**item) for item in memory_dump.get("evidence", [])]
    candidates = _candidate_rows(evidence)
    source_readings = _source_readings(steps)
    comparison_matrix = _scored_comparison_matrix(_basic_comparison_matrix(candidates, workflow.domain, source_readings), workflow.domain)
    recommendations = _recommendations(workflow.domain, candidates, comparison_matrix)
    uncertainties = _uncertainties(steps, candidates)
    return StructuredArtifact(
        summary=_summary(workflow, candidates, evidence),
        candidates=candidates,
        source_readings=source_readings,
        recommendations=recommendations,
        reasoning_outline=_workflow_reasoning_outline(workflow),
        subquestions=_workflow_subquestions(workflow),
        search_plan=_workflow_search_plan(workflow),
        decision_criteria=_workflow_decision_criteria(workflow),
        comparison_matrix=comparison_matrix,
        video_digest=_video_digest(steps),
        multimodal_notes=_multimodal_notes(workflow, steps),
        uncertainties=uncertainties,
        next_actions=_next_actions(workflow.domain, bool(candidates)),
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
            "先把推荐问题拆成预算、类型/场景、品牌型号、核心体验、风险点五类证据。",
            "先用榜单/评测搜索建立候选池，再用具体型号对比搜索交叉验证。",
            "深读候选页面，优先抽取价格、专业评测、用户反馈和缺点。",
            "最终按证据强弱而不是关键词命中顺序给出推荐。",
        ]
    return ["先拆解任务目标和证据需求，再用多轮检索与页面深读交叉验证结论。"]


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
    plan: List[Dict[str, Any]] = []
    for node in workflow.nodes:
        if node.action != "search_web":
            continue
        plan.append(
            {
                "query": node.inputs.get("query"),
                "purpose": node.inputs.get("llm_purpose") or node.instruction,
                "source": node.inputs.get("source"),
                "evidence_stage": node.inputs.get("evidence_stage"),
            }
        )
    return plan[:8]


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


def _summary(workflow: WorkflowSpec, candidates: List[Dict[str, Any]], evidence: List[EvidenceItem]) -> str:
    if candidates:
        return (
            f"Workflow '{workflow.template}' completed for '{workflow.goal}'. "
            f"Collected {len(candidates)} candidate links and {len(evidence)} evidence items."
        )
    return (
        f"Workflow '{workflow.template}' ran for '{workflow.goal}', but candidate extraction was limited. "
        f"Collected {len(evidence)} evidence items."
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
    if comparison_matrix:
        return [
            {
                "rank": idx + 1,
                "name": item.get("name") or item.get("title"),
                "url": item.get("url"),
                "score": item.get("score"),
                "reason": f"{label} Evidence score {item.get('score')}: {', '.join(item.get('score_reasons', []))}",
            }
            for idx, item in enumerate(comparison_matrix[:5])
            if item.get("url")
        ]
    return [
        {
            "rank": idx + 1,
            "name": candidate["name"],
            "url": candidate["url"],
            "reason": label,
        }
        for idx, candidate in enumerate(candidates[:5])
    ]


def _uncertainties(steps: List[Dict[str, Any]], candidates: List[Dict[str, Any]]) -> List[str]:
    uncertainties: List[str] = []
    failed = [step for step in steps if not step.get("ok")]
    if failed:
        uncertainties.append("Some workflow steps failed or required fallback; inspect events for retry details.")
    if not candidates:
        uncertainties.append("No candidate links were extracted; the target page may block automation or require login.")
    return uncertainties or ["This MVP uses rule-based extraction, so ranking quality should be manually reviewed."]


def _next_actions(domain: str, has_candidates: bool) -> List[str]:
    if not has_candidates:
        return ["Try a narrower query or switch to a source-specific URL."]
    if domain == "github":
        return ["Open the top repositories, inspect README/code entrypoints, then verify recent activity."]
    if domain == "paper":
        return ["Open top papers, extract method/dataset/metric fields, then cross-check code availability."]
    return ["Review the top candidates and run a deeper extraction workflow on the best matches."]
