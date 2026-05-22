from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .llm_planner import LLMConfig, request_text_completion
from .memory import AgentMemory
from .schema import Observation


def generate_comparison(
    command: str,
    observation: Observation,
    memory: Optional[AgentMemory] = None,
    llm_config: Optional[LLMConfig] = None,
) -> str:
    """Return human-readable comparison text from current page + memory candidates."""
    candidates = build_candidate_set(observation, memory)
    if len(candidates) < 2:
        return "没有找到足够的候选项用于比较。"
    llm_result = _compare_with_llm(command, observation, candidates, memory, llm_config)
    if llm_result:
        return llm_result
    return _compare_with_rules(command, observation, candidates, memory)


def recommend_from_observation(
    command: str,
    observation: Observation,
    memory: Optional[AgentMemory] = None,
    llm_config: Optional[LLMConfig] = None,
    require_llm: bool = True,
) -> Dict[str, Any]:
    """Return structured recommendation object; can enforce LLM-required mode."""
    candidates = build_candidate_set(observation, memory)
    if len(candidates) < 2:
        return {
            "ok": False,
            "error": "candidate_insufficient",
            "message": "候选数量不足，无法生成可靠推荐。",
            "candidateCount": len(candidates),
            "candidates": candidates,
        }
    llm_result: Dict[str, Any] = {}
    llm_error = ""
    if llm_config and llm_config.enabled:
        try:
            llm_result = _recommend_with_llm_json(command, observation, candidates, memory, llm_config)
        except Exception as exc:
            llm_error = str(exc)
    if require_llm and not llm_result:
        return {
            "ok": False,
            "error": "llm_required_failed",
            "message": llm_error or "LLM 未返回可解析推荐结果。",
            "candidateCount": len(candidates),
            "candidates": candidates,
        }
    if not llm_result:
        text_result = _compare_with_rules(command, observation, candidates, memory)
        winner = candidates[0]["title"] if candidates else ""
        return {
            "ok": True,
            "source": "rule",
            "comparisonTable": _simple_comparison_table(candidates),
            "topPick": winner,
            "why": text_result,
            "evidence": [str(item.get("href") or item.get("source_url") or "") for item in candidates[:6] if str(item.get("href") or item.get("source_url") or "")],
            "confidence": 0.58,
            "candidateCount": len(candidates),
        }
    return {
        "ok": True,
        "source": "python-llm",
        "comparisonTable": llm_result.get("comparisonTable", []),
        "topPick": str(llm_result.get("topPick") or ""),
        "why": str(llm_result.get("why") or ""),
        "evidence": [str(item) for item in llm_result.get("evidence", []) if str(item).strip()],
        "confidence": float(llm_result.get("confidence", 0.0) or 0.0),
        "candidateCount": len(candidates),
    }


def build_candidate_set(observation: Observation, memory: Optional[AgentMemory] = None) -> List[Dict[str, Any]]:
    """Aggregate and normalize candidates from cards, tables, and memory snapshots."""
    candidates: List[Dict[str, Any]] = []
    seen = set()
    for card in observation.cards:
        item = _normalize_candidate(card, observation.url)
        if item["title"] and item["title"] not in seen:
            seen.add(item["title"])
            candidates.append(item)
    for row in _table_candidates(observation):
        if row["title"] and row["title"] not in seen:
            seen.add(row["title"])
            candidates.append(row)
    if memory:
        for snapshot in memory.candidate_snapshots:
            source_url = str(snapshot.get("url") or observation.url)
            for card in snapshot.get("cards", []):
                if not isinstance(card, dict):
                    continue
                item = _normalize_candidate(card, source_url)
                if item["title"] and item["title"] not in seen:
                    seen.add(item["title"])
                    candidates.append(item)
    candidates = _filter_aggregate_candidates(candidates[:16])
    if memory:
        for item in candidates:
            _apply_detail_context(item, memory)
    return candidates


def select_sampling_candidates(
    command: str,
    observation: Observation,
    memory: Optional[AgentMemory] = None,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Pick top candidate detail URLs for follow-up sampling."""
    focus = _clean_compare_focus(command)
    candidates = build_candidate_set(observation, memory)
    ranked = sorted(candidates, key=lambda item: _score_candidate(item, focus, command), reverse=True)
    picked = []
    for item in ranked:
        href = str(item.get("href") or "").strip()
        if not href or href == observation.url:
            continue
        if memory and any(page.get("url") == href for page in memory.detail_pages):
            continue
        picked.append(item)
        if len(picked) >= limit:
            break
    return picked


def _compare_with_rules(command: str, observation: Observation, candidates: List[Dict[str, Any]], memory: Optional[AgentMemory]) -> str:
    focus = _clean_compare_focus(command)
    ranked = sorted(candidates, key=lambda item: _score_candidate(item, focus, command), reverse=True)[:6]
    lines = [
        f"综合比较：{focus or observation.title}",
        f"来源页面：{observation.url}",
        f"候选数量：{len(candidates)}",
    ]
    if memory and memory.summary():
        lines.append(f"记忆上下文：{memory.summary()}")
    if memory and memory.detail_pages:
        lines.append("详情页采样：")
        for index, page in enumerate(memory.detail_pages[:3], 1):
            summary = str(page.get("summary") or "")[:140]
            lines.append(f"{index}. {page.get('candidateTitle') or page.get('pageTitle')}\n   {summary}\n   {page.get('url') or observation.url}")
    lines.append("综合数据表：")
    lines.extend(_render_table(ranked))
    lines.append("候选结论：")
    for index, item in enumerate(ranked, 1):
        metrics = [f"综合分 {item['score']:.1f}"]
        if item.get("price_text"):
            metrics.append(f"价格 {item['price_text']}")
        if item.get("rating_text"):
            metrics.append(f"评分 {item['rating_text']}")
        if item.get("date_text"):
            metrics.append(f"日期 {item['date_text']}")
        if item.get("detail_strength"):
            metrics.append(f"详情强度 {item['detail_strength']}")
        detail = item.get("detail_summary") or "未采到详情页摘要"
        lines.append(
            f"{index}. {item['title']}\n   {' | '.join(metrics)}\n   特征：{item['feature_summary']}\n   详情页洞察：{detail[:180]}\n   来源：{item['href'] or item['source_url']}"
        )
    winner = ranked[0]
    lines.append(f"最终推荐理由：{_winner_reason(winner, ranked[1:3])}")
    return "\n".join(lines)


def _compare_with_llm(
    command: str,
    observation: Observation,
    candidates: List[Dict[str, Any]],
    memory: Optional[AgentMemory],
    llm_config: Optional[LLMConfig],
) -> str:
    if not llm_config or not llm_config.enabled:
        return ""
    payload = {
        "model": llm_config.model,
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一个浏览器商品/方案比较助手。"
                    "请只输出 JSON，格式为 "
                    '{"focus": str, "winner": str, "summary": str, "ranking": [{"title": str, "reason": str, "score": number, "price": str, "rating": str, "date": str, "features": [str]}]}.'
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task": command,
                        "page": {"url": observation.url, "title": observation.title},
                        "memory": memory.to_dict() if memory else {},
                        "candidates": candidates[:10],
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }
    try:
        content = request_text_completion(payload["messages"], llm_config, temperature=0.1)
        parsed = _parse_compare_json(content)
        if not parsed:
            return ""
        return _render_llm_result(parsed, observation, memory)
    except Exception:
        return ""


def _recommend_with_llm_json(
    command: str,
    observation: Observation,
    candidates: List[Dict[str, Any]],
    memory: Optional[AgentMemory],
    llm_config: LLMConfig,
) -> Dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": (
                "你是商品比较助手。只输出 JSON。格式："
                '{"comparisonTable":[{"title":str,"price":str,"sound":str,"performance":str,"comfort":str,"battery":str,"score":number,"reason":str,"url":str}],"topPick":str,"why":str,"evidence":[str],"confidence":number}。'
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "task": command,
                    "page": {"url": observation.url, "title": observation.title},
                    "memory": memory.to_dict() if memory else {},
                    "candidates": candidates[:10],
                },
                ensure_ascii=False,
            ),
        },
    ]
    content = request_text_completion(messages, llm_config, temperature=0.2)
    parsed = _parse_compare_json(content)
    if not parsed:
        raise ValueError("LLM recommendation JSON parse failed")
    table = parsed.get("comparisonTable")
    if not isinstance(table, list):
        raise ValueError("LLM recommendation missing comparisonTable")
    return parsed


def _simple_comparison_table(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    table: List[Dict[str, Any]] = []
    for item in candidates[:6]:
        table.append(
            {
                "title": str(item.get("title") or ""),
                "price": str(item.get("price_text") or ""),
                "sound": "",
                "performance": "",
                "comfort": "",
                "battery": "",
                "score": round(float(item.get("score", 0.0) or 0.0), 2),
                "reason": str(item.get("feature_summary") or ""),
                "url": str(item.get("href") or item.get("source_url") or ""),
            }
        )
    return table


def _parse_compare_json(content: str) -> Dict[str, Any]:
    text = str(content or "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        return {}
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _render_llm_result(data: Dict[str, Any], observation: Observation, memory: Optional[AgentMemory]) -> str:
    ranking = data.get("ranking") if isinstance(data.get("ranking"), list) else []
    lines = [
        f"综合比较：{data.get('focus') or observation.title}",
        f"来源页面：{observation.url}",
    ]
    if memory and memory.summary():
        lines.append(f"记忆上下文：{memory.summary()}")
    lines.append(f"LLM 总结：{data.get('summary') or '未返回总结。'}")
    lines.append("综合数据表：")
    for index, item in enumerate(ranking[:6], 1):
        if not isinstance(item, dict):
            continue
        features = item.get("features") if isinstance(item.get("features"), list) else []
        metrics = [f"分数 {item.get('score', '-')}", f"价格 {item.get('price') or '-'}", f"评分 {item.get('rating') or '-'}"]
        if item.get("date"):
            metrics.append(f"日期 {item.get('date')}")
        lines.append(
            f"{index}. {item.get('title') or '未命名候选'}\n   {' | '.join(metrics)}\n   原因：{item.get('reason') or '未返回原因'}\n   特征：{', '.join(str(feature) for feature in features[:6]) or '未提取到明显特征'}"
        )
    lines.append(f"最终推荐理由：{data.get('winner') or '未返回推荐项'}")
    return "\n".join(lines)


def _table_candidates(observation: Observation) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for table in observation.tables[:3]:
        if len(table) < 2:
            continue
        header = [str(cell).strip() for cell in table[0]]
        lowered = " ".join(header).lower()
        if not re.search(r"功能|价格|评分|日期|方案|产品|name|price|rating|feature|date", lowered):
            continue
        title_index = _first_index(header, ["方案", "产品", "名称", "功能", "name", "product", "tool"])
        price_index = _first_index(header, ["价格", "price", "cost"])
        rating_index = _first_index(header, ["评分", "rating", "score"])
        date_index = _first_index(header, ["日期", "时间", "date", "updated"])
        for row in table[1:]:
            if title_index is None or title_index >= len(row):
                continue
            title = str(row[title_index]).strip()
            summary = "；".join(str(cell).strip() for idx, cell in enumerate(row) if idx != title_index and str(cell).strip())
            items.append(
                {
                    "title": title,
                    "summary": summary,
                    "href": "",
                    "price": str(row[price_index]).strip() if price_index is not None and price_index < len(row) else "",
                    "rating": str(row[rating_index]).strip() if rating_index is not None and rating_index < len(row) else "",
                    "date": str(row[date_index]).strip() if date_index is not None and date_index < len(row) else "",
                }
            )
    return items


def _normalize_candidate(card: Dict[str, Any], source_url: str) -> Dict[str, Any]:
    title = str(card.get("title") or "").strip()
    summary = str(card.get("summary") or "").strip()
    href = str(card.get("href") or "").strip()
    price_text = str(card.get("price") or card.get("price_text") or "").strip()
    rating_text = str(card.get("rating") or card.get("rating_text") or "").strip()
    date_text = str(card.get("date") or _find_date(summary) or "").strip()
    features = _extract_features(f"{title} {summary}")
    item = {
        "title": title,
        "summary": summary,
        "href": href,
        "source_url": source_url,
        "price_text": price_text,
        "rating_text": rating_text,
        "date_text": date_text,
        "price_value": _to_price(price_text),
        "rating_value": _to_rating(rating_text),
        "feature_summary": "、".join(features[:6]) or (summary[:120] if summary else "未提取到明显特征"),
        "detail_summary": "",
        "detail_strength": "",
    }
    item["score"] = 0.0
    return item


def _score_candidate(item: Dict[str, Any], focus: str, command: str) -> float:
    text = f"{item.get('title', '')} {item.get('summary', '')} {item.get('feature_summary', '')}".lower()
    tokens = _focus_tokens(focus)
    score = sum(2.5 for token in tokens if token in text)
    if item.get("rating_value") is not None:
        score += float(item["rating_value"])
    if item.get("price_value") is not None:
        score += 2.0 if float(item["price_value"]) == 0 else max(0.0, 2.0 - min(float(item["price_value"]) / 1000, 2.0))
    score += min(len(item.get("feature_summary", "")) / 60, 2.0)
    if re.search(r"便宜|低价|budget|cheap", command, re.I) and item.get("price_value") is not None:
        score += max(0.0, 3.0 - min(float(item["price_value"]) / 500, 3.0))
    if re.search(r"评分|口碑|best|推荐", command, re.I) and item.get("rating_value") is not None:
        score += float(item["rating_value"]) * 0.5
    if _looks_like_aggregate_title(item.get("title", "")):
        score -= 3.0
    detail_summary = str(item.get("detail_summary") or "")
    if detail_summary:
        score += min(len(detail_summary) / 90.0, 2.8)
        if re.search(r"安装线索|能力点|playwright|chrome|automation|智能体|workflow|extension|llm", detail_summary, re.I):
            score += 1.8
    item["score"] = score
    return score


def _clean_compare_focus(command: str) -> str:
    cleaned = re.sub(r"帮我|请|比较|对比|排序|哪个更好|哪个更适合|推荐|这些|方案|产品|工具|research|compare|rank", " ", command, flags=re.I)
    return re.sub(r"\s+", " ", cleaned).strip()


def _focus_tokens(text: str) -> List[str]:
    stopwords = {"和", "与", "及", "或", "the", "a", "an", "vs", "and", "or", "比较", "推荐"}
    tokens = []
    for token in re.split(r"\s+", text.lower()):
        cleaned = token.strip()
        if not cleaned or cleaned in stopwords:
            continue
        if len(cleaned) == 1 and not cleaned.isdigit():
            continue
        tokens.append(cleaned)
    return tokens


def _extract_features(text: str) -> List[str]:
    parts = re.split(r"[，,。；;、/]", text)
    features = []
    for part in parts:
        snippet = part.strip()
        if 2 <= len(snippet) <= 24 and snippet not in features and not re.search(r"评分|price|¥|\$|日期|date", snippet, re.I):
            features.append(snippet)
    return features[:8]


def _filter_aggregate_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    specific_titles = [item["title"] for item in candidates if item.get("href") and not _looks_like_aggregate_title(item.get("title", ""))]
    filtered = []
    for item in candidates:
        summary = str(item.get("summary") or "")
        referenced_titles = sum(1 for title in specific_titles if title and title in summary)
        if _looks_like_aggregate_title(item.get("title", "")) and referenced_titles >= 2:
            continue
        filtered.append(item)
    return filtered


def _apply_detail_context(item: Dict[str, Any], memory: AgentMemory) -> None:
    match = None
    href = str(item.get("href") or "")
    title = str(item.get("title") or "")
    for page in memory.detail_pages:
        if href and page.get("url") == href:
            match = page
            break
        if title and (page.get("candidateTitle") == title or title.lower() in str(page.get("pageTitle") or "").lower()):
            match = page
            break
    if not match:
        return
    item["detail_summary"] = str(match.get("summary") or "")
    capabilities = match.get("capabilities") if isinstance(match.get("capabilities"), list) else []
    install_steps = match.get("install") if isinstance(match.get("install"), list) else []
    about = str(match.get("about") or "").strip()
    detail_bits = []
    if about:
        detail_bits.append(about[:160])
    if capabilities:
        detail_bits.append("能力点：" + "；".join(str(x) for x in capabilities[:3]))
    if install_steps:
        detail_bits.append("安装线索：" + "；".join(str(x) for x in install_steps[:2]))
    if detail_bits:
        item["detail_summary"] = " | ".join(detail_bits + ([item["detail_summary"]] if item["detail_summary"] else []))
    strength = 0
    if about:
        strength += 1
    if capabilities:
        strength += 1
    if install_steps:
        strength += 1
    item["detail_strength"] = f"{strength}/3" if strength else ""
    headings = match.get("headings") if isinstance(match.get("headings"), list) else []
    if headings and not item["date_text"]:
        item["detail_summary"] = f"{' / '.join(str(h) for h in headings[:4])} | {item['detail_summary']}".strip()


def _render_table(items: List[Dict[str, Any]]) -> List[str]:
    header = "| 候选 | 价格 | 评分 | 日期 | 核心特征 | 详情页洞察 |"
    divider = "| --- | --- | --- | --- | --- | --- |"
    rows = [header, divider]
    for item in items:
        rows.append(
            "| "
            + " | ".join(
                [
                    _table_cell(item.get("title") or "-"),
                    _table_cell(item.get("price_text") or "-"),
                    _table_cell(item.get("rating_text") or "-"),
                    _table_cell(item.get("date_text") or "-"),
                    _table_cell(str(item.get("feature_summary") or "-")[:60]),
                    _table_cell(str(item.get("detail_summary") or "未采样")[:80]),
                ]
            )
            + " |"
        )
    return rows


def _table_cell(value: str) -> str:
    return str(value).replace("\n", " ").replace("|", "/")


def _looks_like_aggregate_title(title: str) -> bool:
    return bool(re.search(r"方案库|列表|合集|结果|搜索|搜索结果|目录|总览|汇总", str(title or ""), re.I))


def _winner_reason(winner: Dict[str, Any], runners_up: List[Dict[str, Any]]) -> str:
    reasons = []
    if winner.get("detail_summary"):
        reasons.append("详情页采样后信息最完整")
    if winner.get("rating_text"):
        reasons.append(f"显式评分线索更强（{winner.get('rating_text')}）")
    if winner.get("price_text"):
        reasons.append(f"成本信息清晰（{winner.get('price_text')}）")
    if winner.get("feature_summary"):
        reasons.append(f"核心能力覆盖更贴合需求：{str(winner.get('feature_summary'))[:48]}")
    baseline = runners_up[0]["score"] if runners_up else None
    gap_text = ""
    if baseline is not None:
        gap = float(winner.get("score", 0.0)) - float(baseline)
        gap_text = f"，综合分领先约 {gap:.1f}"
    return f"优先选择“{winner['title']}”，因为它{ '、'.join(reasons[:3]) or '综合表现更均衡' }{gap_text}。"


def _find_date(text: str) -> str:
    match = re.search(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b", text)
    return match.group(1) if match else ""


def _to_price(value: str) -> Optional[float]:
    if not value:
        return None
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", value.replace(",", ""))
    return float(match.group(1)) if match else None


def _to_rating(value: str) -> Optional[float]:
    if not value:
        return None
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", value)
    return float(match.group(1)) if match else None


def _first_index(header: List[str], keywords: List[str]) -> Optional[int]:
    for index, cell in enumerate(header):
        lowered = str(cell).lower()
        if any(keyword.lower() in lowered for keyword in keywords):
            return index
    return None
