from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, Iterable, List, Optional


VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


@dataclass
class Node:
    tag: str
    attrs: Dict[str, str] = field(default_factory=dict)
    children: List["Node"] = field(default_factory=list)
    data: List[str] = field(default_factory=list)
    parent: Optional["Node"] = None

    def text(self) -> str:
        if self.tag in {"script", "style", "noscript"}:
            return ""
        chunks = list(self.data)
        for child in self.children:
            chunks.append(child.text())
        return normalize_space(" ".join(chunks))

    def attr(self, name: str, default: str = "") -> str:
        value = self.attrs.get(name, default)
        return default if value is None else str(value)

    def find_all(self, tags: Optional[Iterable[str]] = None) -> List["Node"]:
        wanted = set(tags) if tags else None
        found: List[Node] = []
        for child in self.children:
            if wanted is None or child.tag in wanted:
                found.append(child)
            found.extend(child.find_all(wanted))
        return found

    def first(self, tags: Iterable[str]) -> Optional["Node"]:
        found = self.find_all(tags)
        return found[0] if found else None


class TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.current = self.root

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        node = Node(tag.lower(), dict(attrs), parent=self.current)
        self.current.children.append(node)
        if tag.lower() not in VOID_TAGS:
            self.current = node

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        node = self.current
        while node.parent and node.tag != tag:
            node = node.parent
        if node.parent:
            self.current = node.parent

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.current.data.append(data)


def parse_html(html: str) -> Node:
    parser = TreeParser()
    parser.feed(html)
    return parser.root


def normalize_space(text: str) -> str:
    return " ".join(text.split())
