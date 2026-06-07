from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


def render_markdown_report(result: Dict[str, Any]) -> str:
    report = result.get("report", {}) if isinstance(result.get("report"), dict) else {}
    workflow = result.get("workflow", {}) if isinstance(result.get("workflow"), dict) else {}
    title = _clean(result.get("goal") or workflow.get("goal") or "Browser Agent Report")
    lines: List[str] = [
        f"# {title}",
        "",
        f"- Run ID: `{_clean(result.get('run_id', ''))}`",
        f"- Domain: `{_clean(workflow.get('domain', 'unknown'))}`",
        f"- Status: `{_clean('ok' if result.get('ok') else 'needs_review')}`",
        f"- Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
    ]
    _section(lines, "Summary", [_clean(report.get("summary") or "No summary available.")])
    progression_rendered = _requirement_progression(lines, report.get("requirement_progression"))
    _section(lines, "Action Rationale", _list_text(report.get("reasoning_outline")))
    _section(lines, "Subquestions", _list_text(report.get("subquestions")))
    if not progression_rendered and not report.get("reasoning_outline"):
        _search_plan(lines, report.get("evidence_plan") or report.get("search_plan"))
    _recommendations(lines, report.get("recommendations"))
    _comparison(lines, report.get("comparison_matrix"), workflow.get("domain"))
    _source_readings(lines, report.get("source_readings"))
    _video_digest(lines, report.get("video_digest"))
    _multimodal(lines, report.get("multimodal_notes"))
    _failure_analysis(lines, report.get("failure_analysis") or result.get("failure_analysis"))
    _section(lines, "Uncertainties", _list_text(report.get("uncertainties")))
    _section(lines, "Next Actions", _list_text(report.get("next_actions")))
    _citations(lines, report.get("citations"))
    return "\n".join(lines).rstrip() + "\n"


def _section(lines: List[str], title: str, items: List[str]) -> None:
    if not items:
        return
    lines.extend([f"## {title}", ""])
    for item in items:
        lines.append(f"- {item}")
    lines.append("")


def _search_plan(lines: List[str], plan: Any) -> bool:
    if not isinstance(plan, list) or not plan:
        return False
    lines.extend(["## Evidence Plan", ""])
    for item in plan[:8]:
        if not isinstance(item, dict):
            continue
        purpose = _clean(item.get("purpose") or "Evidence step")
        hint = _clean(item.get("evidence_hint") or item.get("query") or "")
        source = _clean(item.get("source") or "")
        lines.append(f"- **{purpose}** (`{source}`): evidence hint `{hint}`")
    lines.append("")
    return True


def _requirement_progression(lines: List[str], progression: Any) -> bool:
    if not isinstance(progression, list) or not progression:
        return False
    lines.extend(["## Requirement Progression", ""])
    for item in progression[:8]:
        if not isinstance(item, dict):
            continue
        slot = _clean(item.get("requirement_slot") or item.get("purpose") or "slot")
        status = _clean(item.get("status") or "missing")
        evidence = _clean(item.get("evidence_summary") or "")
        latest_action = _clean(item.get("latest_action") or "")
        latest_url = _clean(item.get("latest_url") or "")
        line = f"- **{slot}** `{status}`"
        if latest_action:
            line += f" via `{latest_action}`"
        if latest_url:
            line += f" - {latest_url}"
        lines.append(line)
        if evidence:
            lines.append(f"  - Current evidence: {evidence}")
    lines.append("")
    return True


def _recommendations(lines: List[str], recommendations: Any) -> None:
    if not isinstance(recommendations, list) or not recommendations:
        return
    lines.extend(["## Recommendations", ""])
    for item in recommendations[:8]:
        if not isinstance(item, dict):
            continue
        name = _clean(item.get("name") or item.get("title") or "Recommendation")
        url = _clean(item.get("url") or "")
        score = item.get("score")
        reason = _clean(item.get("reason") or "")
        prefix = f"- **{name}**"
        if url:
            prefix += f" - {url}"
        if score is not None:
            prefix += f"\n  - Score: `{score}`"
        if reason:
            prefix += f"\n  - Reason: {reason}"
        lines.append(prefix)
    lines.append("")


def _comparison(lines: List[str], rows: Any, domain: Any) -> None:
    if not isinstance(rows, list) or not rows:
        return
    lines.extend(["## Comparison Matrix", ""])
    headers = ["Name", "Score", "Evidence", "Key Signals", "URL"]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows[:10]:
        if not isinstance(row, dict):
            continue
        signals = _signals(row, str(domain or ""))
        values = [
            _table(_clean(row.get("name") or row.get("title") or "")),
            _table(_clean(row.get("score", ""))),
            _table(_clean(", ".join(str(x) for x in row.get("score_reasons", [])) or row.get("fit_notes", ""))),
            _table(signals),
            _table(_clean(row.get("url") or "")),
        ]
        lines.append("| " + " | ".join(values) + " |")
    lines.append("")


def _source_readings(lines: List[str], readings: Any) -> None:
    if not isinstance(readings, list) or not readings:
        return
    lines.extend(["## Source Readings", ""])
    for item in readings[:8]:
        if not isinstance(item, dict):
            continue
        title = _clean(item.get("name") or item.get("title") or "Source")
        url = _clean(item.get("url") or "")
        desc = _clean(item.get("description") or item.get("text") or "")[:300]
        lines.append(f"- **{title}** - {url}")
        if desc:
            lines.append(f"  - Evidence: {desc}")
    lines.append("")


def _video_digest(lines: List[str], digest: Any) -> None:
    if not isinstance(digest, dict) or not digest:
        return
    lines.extend(["## Video Digest", ""])
    for key in ["title", "url", "screenshot_path"]:
        if digest.get(key):
            lines.append(f"- {key}: `{_clean(digest.get(key))}`")
    keyframes = digest.get("keyframes")
    if isinstance(keyframes, dict):
        lines.append(f"- keyframes: `{_clean(keyframes.get('status') or keyframes.get('reason'))}`")
        if keyframes.get("reason"):
            lines.append(f"- keyframe_reason: `{_clean(keyframes.get('reason'))}`")
    if digest.get("visual_inputs"):
        lines.append(f"- visual_inputs: `{_clean(digest.get('visual_inputs'))}`")
    transcript = _clean(digest.get("visible_transcript") or "")[:500]
    if transcript:
        lines.extend(["", "### Transcript / Visible Text", "", transcript])
    lines.append("")


def _multimodal(lines: List[str], notes: Any) -> None:
    if not isinstance(notes, list) or not notes:
        return
    lines.extend(["## Multimodal Notes", ""])
    for item in notes[:6]:
        if not isinstance(item, dict):
            continue
        provider = _clean(item.get("provider") or "vision")
        status = _clean(item.get("status") or "")
        reason = _clean(item.get("finding") or item.get("reason") or item.get("purpose") or "")
        lines.append(f"- **{provider}** `{status}`: {reason}")
    lines.append("")


def _failure_analysis(lines: List[str], rows: Any) -> None:
    if not isinstance(rows, list) or not rows:
        return
    lines.extend(["## Failure Analysis", ""])
    for item in rows[:8]:
        if not isinstance(item, dict):
            continue
        failure_type = _clean(item.get("failure_type") or "unknown_failure")
        count = _clean(item.get("count") or 0)
        latest = item.get("latest_example") if isinstance(item.get("latest_example"), dict) else {}
        action = _clean(latest.get("action") or "")
        error = _clean(latest.get("error") or "")
        line = f"- **{failure_type}**: `{count}`"
        if action:
            line += f" latest action `{action}`"
        lines.append(line)
        if error:
            lines.append(f"  - Example: {error}")
    lines.append("")


def _citations(lines: List[str], citations: Any) -> None:
    if not isinstance(citations, list) or not citations:
        return
    lines.extend(["## Citations", ""])
    for item in citations[:12]:
        if not isinstance(item, dict):
            continue
        lines.append(f"- {_clean(item.get('source_url') or '')} - {_clean(item.get('claim') or '')}")
    lines.append("")


def _signals(row: Dict[str, Any], domain: str) -> str:
    if domain == "github":
        return ", ".join(_clean(x) for x in [
            f"stars={row.get('stars')}" if row.get("stars") is not None else "",
            f"language={row.get('language')}" if row.get("language") else "",
            f"license={row.get('license')}" if row.get("license") else "",
            f"updated={row.get('updated_at')}" if row.get("updated_at") else "",
        ] if x)
    if domain == "shopping":
        return ", ".join(_clean(x) for x in [row.get("price_signal"), row.get("fit_notes")] if x)
    if domain == "video":
        return _clean(row.get("snippet") or row.get("description") or row.get("fit_notes") or "")[:160]
    return _clean(row.get("snippet") or row.get("description") or "")[:160]


def _list_text(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [_clean(item) for item in value if _clean(item)]


def _clean(value: Any) -> str:
    text = str(value if value is not None else "")
    return text.replace("\r", " ").replace("\n", " ").strip()


def _table(value: Any) -> str:
    return _clean(value).replace("|", "\\|")
