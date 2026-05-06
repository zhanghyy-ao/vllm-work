from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .comparison import generate_comparison
from .llm_planner import LLMConfig
from .memory import AgentMemory
from .schema import Action, ActionResult, Element, ExecutionResult, Observation, Plan


@dataclass
class BrowserHarness:
    observation: Observation
    llm_config: Optional[LLMConfig] = None
    memory: Optional[AgentMemory] = None
    values: Dict[str, str] = field(default_factory=dict)
    highlighted: List[str] = field(default_factory=list)
    clipboard: str = ""
    artifact: str = ""
    synthetic_blocks: List[str] = field(default_factory=list)

    def run(self, plan: Plan) -> ExecutionResult:
        logs: List[ActionResult] = []
        for action in plan.actions:
            try:
                output = self.execute(action)
                logs.append(ActionResult(action=action, ok=True, output=output))
            except Exception as exc:  # pragma: no cover - kept for defensive logging
                logs.append(ActionResult(action=action, ok=False, error=str(exc)))
                break
        return ExecutionResult(url=self.observation.url, logs=logs, artifact=self.artifact)

    def execute(self, action: Action) -> Any:
        if action.type == "navigate":
            self.observation.url = str(action.value)
            return {"url": self.observation.url}
        if action.type == "highlight":
            target = self._target(action.target_id)
            self.highlighted.append(target.id)
            return {"targetId": target.id}
        if action.type == "type":
            target = self._target(action.target_id)
            self.values[target.id] = str(action.value or "")
            return {"targetId": target.id, "value": self.values[target.id]}
        if action.type == "press":
            target = self._target(action.target_id)
            if (action.key or "Enter") == "Enter":
                self._maybe_submit_search(target)
            return {"targetId": target.id, "key": action.key or "Enter"}
        if action.type == "click":
            target = self._target(action.target_id)
            self.highlighted.append(target.id)
            self._maybe_submit_search(target)
            return {"targetId": target.id}
        if action.type == "scroll":
            return {"scrolled": action.value or 600}
        if action.type == "wait":
            return {"waited": action.value or 1000}
        if action.type == "extract":
            snippets = self.extract(str(action.value or ""))
            self.artifact = "\n\n".join(snippets) if snippets else "没有提取到明显相关片段。"
            return snippets
        if action.type == "summarize":
            self.artifact = self.summarize()
            return self.artifact
        if action.type == "collect":
            data = self.collect(str(action.value or "cards"))
            self.artifact = json.dumps(data, ensure_ascii=False, indent=2)
            return data
        if action.type == "compare":
            self.artifact = self.compare(str(action.value or ""))
            return self.artifact
        if action.type == "brief":
            self.artifact = self.brief(str(action.value or "research"))
            return self.artifact
        if action.type == "find":
            self.artifact = self.find_on_page(str(action.value or ""))
            return self.artifact
        if action.type == "copy":
            self.clipboard = self.artifact or "暂无可复制内容。"
            return {"copied": True, "length": len(self.clipboard)}
        raise ValueError(f"Unsupported action type: {action.type}")

    def extract(self, keyword: str) -> List[str]:
        tokens = [token.lower() for token in re.split(r"\s+", keyword) if token.strip()]
        blocks = [
            self.observation.title,
            *[card["title"] + " " + card.get("summary", "") for card in self.observation.cards],
            *self.synthetic_blocks,
            *[line.strip() for line in re.split(r"[。！？\n]", self.observation.text) if len(line.strip()) >= 12],
        ]
        scored = []
        for block in blocks:
            lower = block.lower()
            score = sum(1 for token in tokens if token and token in lower)
            if score > 0 or not tokens:
                scored.append((score, block[:280]))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [f"{index + 1}. {text}" for index, (_score, text) in enumerate(scored[:5])]

    def summarize(self) -> str:
        bullets = []
        for heading in self.observation.headings[:4]:
            bullets.append(f"页面标题：{heading}")
        for card in self.observation.cards[:4]:
            bullets.append(f"页面模块：{card['title']} - {card.get('summary', '')[:120]}")
        sentences = [line.strip() for line in re.split(r"[。！？\n]", self.observation.text) if 18 <= len(line.strip()) <= 160]
        for sentence in sentences:
            if sentence not in bullets:
                bullets.append(sentence)
            if len(bullets) >= 6:
                break
        return "\n".join([f"页面摘要：{self.observation.title}", *[f"{i + 1}. {item}" for i, item in enumerate(bullets[:6])]])

    def collect(self, kind: str) -> Dict[str, Any]:
        base = {
            "kind": kind,
            "sourceUrl": self.observation.url,
            "collectedAt": datetime.now(timezone.utc).isoformat(),
        }
        if kind == "links":
            return {**base, "items": self.observation.links[:20]}
        if kind == "emails":
            return {**base, "items": self.observation.emails}
        if kind == "contacts":
            return {**base, "emails": self.observation.emails, "links": self.observation.links[:20]}
        if kind == "prices":
            return {**base, "items": self.observation.prices}
        if kind == "tables":
            return {**base, "items": self.observation.tables[:5]}
        return {**base, "items": self.observation.cards[:12]}

    def brief(self, kind: str) -> str:
        if kind == "github":
            return self.github_brief()
        if kind == "docs":
            return self.docs_brief()
        if kind == "ui":
            return self.ui_brief()
        if kind == "project":
            return self.project_brief()
        return self.research_brief()

    def research_brief(self) -> str:
        source_items = []
        for index, card in enumerate(self.observation.cards[:6], 1):
            source_items.append(f"{index}. {card['title']}\n   {card.get('summary', '')}\n   {card.get('href') or self.observation.url}")
        if not source_items:
            for index, link in enumerate(self.observation.links[:6], 1):
                source_items.append(f"{index}. {link['text']}\n   {link['href']}")
        return "\n".join(
            [
                f"研究简报：{self.observation.title}",
                f"来源：{self.observation.url}",
                "核心材料：",
                *(source_items or ["1. 当前页面没有明显结果卡片或链接。"]),
                "下一步建议：优先打开最相关的 2--3 个来源，提取安装方式、使用限制和可复现实验入口。",
            ]
        )

    def github_brief(self) -> str:
        key_links = [
            link
            for link in self.observation.links
            if re.search(r"issues|pull|releases|license|readme|docs|wiki|github", f"{link['text']} {link['href']}", re.I)
        ][:8]
        about = self.observation.cards[0]["summary"] if self.observation.cards else ""
        return "\n".join(
            [
                f"GitHub 仓库简报：{self.observation.title}",
                f"来源：{self.observation.url}",
                f"项目简介：{about[:360] if about else '未在当前可见区域提取到 About 信息。'}",
                f"README/页面结构：{' / '.join(self.observation.headings[:8]) or '未提取到标题'}",
                "关键链接：",
                *([f"{i + 1}. {link['text']} - {link['href']}" for i, link in enumerate(key_links)] or ["1. 当前页未提取到明显关键链接。"]),
                "工程判断：优先检查 README 的安装步骤、License、最近提交和 issue 活跃度，再决定是否作为课程 Demo 基座。",
            ]
        )

    def docs_brief(self) -> str:
        snippets = self.extract("install 安装 setup 配置 API key token playwright browser")
        code_like = [line for line in re.split(r"\n|。", self.observation.text) if re.search(r"pip|npm|pnpm|install|API|key|token|配置|安装", line, re.I)][:5]
        return "\n".join(
            [
                f"文档页简报：{self.observation.title}",
                f"来源：{self.observation.url}",
                f"页面结构：{' / '.join(self.observation.headings[:10]) or '未提取到标题'}",
                "相关片段：",
                *(snippets or ["1. 当前可见区域没有匹配到明显安装/配置/API 片段。"]),
                "代码/命令线索：",
                *([f"{i + 1}. {text[:240]}" for i, text in enumerate(code_like)] or ["1. 当前可见区域没有明显代码/命令线索。"]),
            ]
        )

    def ui_brief(self) -> str:
        groups: Dict[str, int] = {}
        for element in self.observation.elements:
            key = element.role or element.tag
            groups[key] = groups.get(key, 0) + 1
        risky = [
            element
            for element in self.observation.elements
            if re.search(r"提交|发送|删除|付款|支付|发布|上传|submit|send|delete|pay|publish|upload", element.haystack(), re.I)
        ][:8]
        workflows = self._infer_workflows()
        workflow_lines = [f"{i + 1}. {item}" for i, item in enumerate(workflows or ["未识别到明显工作流。"])]
        risky_lines = [f"{i + 1}. {element.label or element.text or element.id}" for i, element in enumerate(risky)] or ["1. 当前可见区域未发现明显高风险按钮。"]
        return "\n".join(
            [
                f"界面分析：{self.observation.title}",
                f"来源：{self.observation.url}",
                f"可交互元素：{len(self.observation.elements)} 个",
                "控件分布：" + ("，".join(f"{key}={value}" for key, value in groups.items()) or "无"),
                "可能工作流：",
                *workflow_lines,
                "需要谨慎确认的按钮：",
                *risky_lines,
            ]
        )

    def project_brief(self) -> str:
        key_links = [
            link
            for link in self.observation.links
            if re.search(r"github|docs|readme|license|issue|demo|paper|arxiv|playwright|browser", f"{link['text']} {link['href']}", re.I)
        ][:10]
        return "\n".join(
            [
                f"项目分析：{self.observation.title}",
                f"来源：{self.observation.url}",
                f"页面/项目结构：{' / '.join(self.observation.headings[:10]) or '未提取到标题'}",
                "模块或候选项：",
                *([f"{i + 1}. {card['title']} - {card.get('summary', '')}" for i, card in enumerate(self.observation.cards[:8])] or ["1. 当前页面没有明显卡片模块。"]),
                "关键资源链接：",
                *([f"{i + 1}. {link['text']} - {link['href']}" for i, link in enumerate(key_links)] or ["1. 当前页面没有明显项目资源链接。"]),
                "可复用性判断：优先复用动作 schema、页面观测、日志/评测模块；对真实提交、发送、支付类动作保持人工确认。",
            ]
        )

    def find_on_page(self, query: str) -> str:
        snippets = self.extract(query)
        matched = [element for element in self.observation.elements if _score_text(element.haystack(), query) > 0][:6]
        if matched:
            self.highlighted.append(matched[0].id)
        return "\n".join(
            [
                f"页面查找：{query}",
                f"来源：{self.observation.url}",
                "相关片段：",
                *(snippets or ["1. 没有找到明显文本片段。"]),
                "相关可操作元素：",
                *([f"{i + 1}. {element.label or element.text or element.placeholder or element.id} ({element.role or element.tag})" for i, element in enumerate(matched)] or ["1. 没有匹配到可操作元素。"]),
            ]
        )

    def _infer_workflows(self) -> List[str]:
        text = " ".join(element.haystack() for element in self.observation.elements)
        workflows = []
        if re.search(r"搜索|search|query|关键词", text, re.I):
            workflows.append("搜索/检索信息")
        if re.search(r"姓名|邮箱|email|name|message|备注|表单|contact", text, re.I):
            workflows.append("填写表单或联系信息")
        if re.search(r"回复|消息|评论|chat|reply|message", text, re.I):
            workflows.append("生成消息或评论草稿")
        if re.search(r"下载|download|导出|export", text, re.I):
            workflows.append("下载或导出资料")
        if re.search(r"筛选|排序|filter|sort", text, re.I):
            workflows.append("筛选、排序或比较结果")
        return workflows

    def compare(self, command: str) -> str:
        return generate_comparison(command, self.observation, memory=self.memory, llm_config=self.llm_config)

    def _target(self, target_id: Optional[str]) -> Element:
        for element in self.observation.elements:
            if element.id == target_id:
                return element
        raise ValueError(f"Target not found: {target_id}")

    def _maybe_submit_search(self, target: Element) -> None:
        target_text = target.haystack()
        if "搜索" not in target_text and "search" not in target_text:
            return
        query = self._latest_search_query()
        if query:
            self.synthetic_blocks.insert(0, f"{query}：自动搜索结果 这是一条由 Python Harness 生成的搜索结果。")

    def _latest_search_query(self) -> str:
        for element_id, value in reversed(list(self.values.items())):
            element = self._find_element(element_id)
            if element and ("search" in element.haystack() or "搜索" in element.haystack()):
                return value
        return ""

    def _find_element(self, element_id: str) -> Optional[Element]:
        return next((element for element in self.observation.elements if element.id == element_id), None)


def _score_text(text: str, query: str) -> int:
    haystack = str(text or "").lower()
    return sum(1 for token in str(query or "").lower().split() if token and token in haystack)
