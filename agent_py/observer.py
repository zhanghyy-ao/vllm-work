from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

from .html_model import Node, normalize_space, parse_html
from .schema import Element, Observation


INTERACTIVE_TAGS = {"a", "button", "input", "textarea", "select"}
INTERACTIVE_ROLES = {"button", "link", "textbox", "searchbox", "combobox", "menuitem", "option"}


def observe_html(html: str, url: str = "about:blank") -> Observation:
    root = parse_html(html)
    title_node = root.first(["title"])
    title = title_node.text() if title_node else ""
    text = root.text()
    labels = _labels_by_for(root)

    elements: List[Element] = []
    for node in root.find_all():
        if not _is_interactive(node):
            continue
        element_id = f"e{len(elements) + 1}"
        label = _label_for(node, labels)
        role = node.attr("role") or _implicit_role(node)
        elements.append(
            Element(
                id=element_id,
                tag=node.tag,
                selector=_selector_for(node),
                role=role,
                type=node.attr("type"),
                name=node.attr("name"),
                label=label,
                text=node.text()[:160],
                placeholder=node.attr("placeholder"),
                href=urljoin(url, node.attr("href")) if node.attr("href") else "",
                value=node.attr("value"),
                form_id=_ancestor_attr(node, "form", "id"),
                section_label=_section_label(node),
                visible=True,
                enabled=node.attr("disabled").lower() not in {"", "disabled", "true"} if node.attr("disabled") else True,
                content_editable=node.attr("contenteditable").lower() == "true",
                clickable=bool(node.attr("onclick")),
            )
        )

    return Observation(
        url=url,
        title=title,
        text=text[:10000],
        elements=elements,
        cards=_collect_cards(root, url),
        tables=_collect_tables(root),
        links=_collect_links(root, url),
        emails=sorted(set(re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I))),
        prices=sorted(set(re.findall(r"(?:¥|\$|￥)\s?\d+(?:\.\d{1,2})?", text))),
        headings=[node.text() for node in root.find_all(["h1", "h2", "h3"]) if node.text()],
    )


def _css_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _selector_for(node: Node) -> str:
    node_id = node.attr("id")
    if node_id:
        return f'#{_css_escape(node_id)}'
    name = node.attr("name")
    if name:
        return f'{node.tag}[name="{_css_escape(name)}"]'
    aria = node.attr("aria-label")
    if aria:
        return f'{node.tag}[aria-label="{_css_escape(aria)}"]'
    href = node.attr("href")
    if href:
        return f'{node.tag}[href="{_css_escape(href)}"]'
    return node.tag


def _ancestor_attr(node: Node, tag: str, attr: str) -> str:
    parent = node.parent
    while parent:
        if parent.tag == tag:
            return parent.attr(attr)
        parent = parent.parent
    return ""


def _section_label(node: Node) -> str:
    parent = node.parent
    while parent:
        if parent.tag in {"section", "article", "form", "main"}:
            aria = parent.attr("aria-label")
            if aria:
                return normalize_space(aria)
            heading = parent.first(["h1", "h2", "h3"])
            if heading:
                return heading.text()
        parent = parent.parent
    return ""


def observe_file(path: str, url: Optional[str] = None) -> Observation:
    html = Path(path).read_text(encoding="utf-8")
    return observe_html(html, url or Path(path).resolve().as_uri())


def _labels_by_for(root: Node) -> Dict[str, str]:
    labels = {}
    for label in root.find_all(["label"]):
        target = label.attr("for")
        if target:
            labels[target] = label.text()
    return labels


def _label_for(node: Node, labels: Dict[str, str]) -> str:
    aria = node.attr("aria-label")
    if aria:
        return normalize_space(aria)
    node_id = node.attr("id")
    if node_id and node_id in labels:
        return labels[node_id]
    if node.parent and node.parent.tag == "label":
        return node.parent.text()
    return ""


def _is_interactive(node: Node) -> bool:
    role = node.attr("role")
    return (
        node.tag in INTERACTIVE_TAGS
        or role in INTERACTIVE_ROLES
        or node.attr("contenteditable").lower() == "true"
        or bool(node.attr("onclick"))
        or bool(node.attr("aria-label") and node.tag not in {"section", "article"})
    )


def _implicit_role(node: Node) -> str:
    if node.tag == "a":
        return "link"
    if node.tag == "button":
        return "button"
    if node.tag == "textarea":
        return "textbox"
    if node.tag == "select":
        return "combobox"
    if node.tag == "input":
        input_type = node.attr("type") or "text"
        if input_type in {"button", "submit", "reset"}:
            return "button"
        if input_type == "search":
            return "searchbox"
        return "textbox"
    return ""


def _collect_links(root: Node, url: str) -> List[Dict[str, str]]:
    seen = set()
    links: List[Dict[str, str]] = []
    for node in root.find_all(["a"]):
        href = node.attr("href")
        if not href:
            continue
        absolute = urljoin(url, href)
        if absolute in seen:
            continue
        seen.add(absolute)
        links.append({"text": node.text() or absolute, "href": absolute})
    return links


def _collect_cards(root: Node, url: str) -> List[Dict[str, str]]:
    cards = []
    for node in root.find_all(["article", "section"]):
        if not (node.attr("data-agent-result") or node.attr("data-agent-card") or "card" in node.attr("class")):
            continue
        title_node = node.first(["h1", "h2", "h3", "a", "strong"])
        title = title_node.text() if title_node else node.text()[:60]
        summary = node.text().replace(title, "", 1).strip()[:280]
        if not title or not summary:
            continue
        link_node = node.first(["a"])
        text = node.text()
        price = re.search(r"(?:¥|\$|￥)\s?\d+(?:\.\d{1,2})?", text)
        rating = re.search(r"(?:评分|rating|score)[:： ]?\s?([0-9](?:\.[0-9])?)", text, re.I)
        cards.append(
            {
                "title": title,
                "summary": summary,
                "href": urljoin(url, link_node.attr("href")) if link_node and link_node.attr("href") else "",
                "price": price.group(0) if price else "",
                "rating": rating.group(1) if rating else "",
            }
        )
    return _unique_by(cards, "title")


def _collect_tables(root: Node) -> List[List[List[str]]]:
    tables: List[List[List[str]]] = []
    for table in root.find_all(["table"]):
        rows = []
        for row in table.find_all(["tr"]):
            cells = [cell.text() for cell in row.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def _unique_by(items: List[Dict[str, str]], key: str) -> List[Dict[str, str]]:
    seen = set()
    unique = []
    for item in items:
        value = item.get(key, "")
        if value in seen:
            continue
        seen.add(value)
        unique.append(item)
    return unique
