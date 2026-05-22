from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .comparison import select_sampling_candidates
from .llm_planner import LLMConfig
from .memory import AgentMemory
from .observer import observe_html
from .schema import Element
from .schema import Action, ActionResult, ExecutionResult, Observation, Plan


INTERACTIVE_SELECTOR = ",".join(
    [
        "a[href]",
        "button",
        "input",
        "textarea",
        "select",
        "[role='button']",
        "[role='link']",
        "[role='textbox']",
        "[contenteditable='true']",
        "[onclick]",
    ]
)


class PlaywrightBrowserRuntime:
    """Live runtime wrapper around Playwright for real browser automation."""
    def __init__(
        self,
        headless: bool = False,
        slow_mo: int = 0,
        cdp_url: str = "",
        screenshot_dir: str = "runs/screenshots",
        llm_config: Optional[LLMConfig] = None,
        memory: Optional[AgentMemory] = None,
    ) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - exercised when dependency missing
            raise RuntimeError("Playwright is not installed. Run: python3 -m pip install -r requirements.txt") from exc

        self._sync_playwright = sync_playwright
        self._playwright = None
        self.browser = None
        self.page = None
        self.headless = headless
        self.slow_mo = slow_mo
        self.cdp_url = cdp_url
        self.connected_over_cdp = False
        self.connection_error = ""
        self.screenshot_dir = screenshot_dir
        self.llm_config = llm_config
        self.memory = memory
        self.observation_count = 0
        self.last_observation: Optional[Observation] = None
        self.artifact = ""
        self.clipboard = ""

    def __enter__(self) -> "PlaywrightBrowserRuntime":
        self.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def start(self) -> None:
        """Initialize Playwright and prefer CDP attach before launching temp Chromium."""
        if self.page:
            return
        self._playwright = self._sync_playwright().start()
        if self.cdp_url:
            try:
                self.browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
                self.connected_over_cdp = True
                context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context(viewport={"width": 1280, "height": 900})
                self.page = self._select_active_page(context)
            except Exception as exc:
                self.connection_error = str(exc)
                self.connected_over_cdp = False
        if not self.page:
            self.browser = self._playwright.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
            self.page = self.browser.new_page(viewport={"width": 1280, "height": 900})

    def close(self) -> None:
        # With connect_over_cdp, browser.close() disconnects Playwright from
        # the remote debugging session without terminating the user-owned Chrome.
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
        self.browser = None
        self.page = None
        self._playwright = None

    def goto(self, url: str) -> Observation:
        self._ensure_page()
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return self.observe()

    def observe(self) -> Observation:
        """Capture a fresh, normalized observation from the active page."""
        self._ensure_page()
        observation = self._build_observation(self.page, capture_screenshot=True)
        self.last_observation = observation
        return observation

    def _build_observation(self, page: Any, capture_screenshot: bool) -> Observation:
        html = ""
        for attempt in range(4):
            try:
                html = page.content()
                break
            except Exception:
                if attempt == 3:
                    raise
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    page.wait_for_timeout(500)
        observation = observe_html(html, page.url)
        live_elements = self._live_elements(page)
        if live_elements:
            observation.elements = live_elements
        observation.screenshot_path = self._capture_observation_screenshot(page) if capture_screenshot else ""
        observation.viewport = page.viewport_size or {}
        return observation

    def screenshot(self, path: str) -> str:
        self._ensure_page()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=path, full_page=False)
        return path

    def run(self, plan: Plan) -> ExecutionResult:
        """Execute actions sequentially, collecting per-step logs and observation trajectory."""
        logs = []
        trajectory = []
        for action in plan.actions:
            try:
                output = self.execute(action)
                observation = self.observe()
                result = ActionResult(action=action, ok=True, output=output, url=observation.url, artifact=self.artifact)
                logs.append(result)
                entry = result.to_dict()
                entry["observation"] = self._observation_summary(observation)
                trajectory.append(entry)
            except Exception as exc:
                url = self.page.url if self.page else ""
                result = ActionResult(action=action, ok=False, error=str(exc), url=url, artifact=self.artifact)
                logs.append(result)
                trajectory.append(result.to_dict())
                break
        return ExecutionResult(url=self.page.url if self.page else "", logs=logs, artifact=self.artifact, trajectory=trajectory)

    def execute(self, action: Action) -> Any:
        """Execute a single action on the page and return structured action output."""
        self._ensure_page()
        if action.type == "navigate":
            self.page.goto(str(action.value), wait_until="domcontentloaded", timeout=30000)
            return {"url": self.page.url}
        if action.type == "scroll":
            self.page.mouse.wheel(0, int(action.value or 700))
            return {"scrolled": action.value or 700}
        if action.type == "wait":
            self.page.wait_for_timeout(int(action.value or 1000))
            return {"waited": action.value or 1000}
        if action.type in {"highlight", "click", "type", "press"}:
            locator = self._locator_for(action.target_id)
            if action.type == "highlight":
                self._highlight_locator(locator)
                return {"targetId": action.target_id}
            if action.type == "click":
                before = self.page.url
                self._click_locator(locator)
                self._wait_after_action(before)
                return {"targetId": action.target_id, "url": self.page.url}
            if action.type == "type":
                locator.fill(str(action.value or ""), timeout=8000)
                return {"targetId": action.target_id, "value": action.value}
            if action.type == "press":
                before = self.page.url
                locator.press(action.key or "Enter", timeout=8000)
                self._wait_after_action(before)
                return {"targetId": action.target_id, "key": action.key or "Enter", "url": self.page.url}
        if action.type == "extract":
            snippets = self._extract(str(action.value or ""))
            self.artifact = "\n\n".join(snippets) if snippets else "没有提取到明显相关片段。"
            return snippets
        if action.type == "summarize":
            self.artifact = self._static_result("summarize")
            return self.artifact
        if action.type == "collect":
            data = self._collect(str(action.value or "cards"))
            self.artifact = json.dumps(data, ensure_ascii=False, indent=2)
            return data
        if action.type == "compare":
            self._sample_detail_pages(str(action.value or ""))
            self.artifact = self._compare(str(action.value or ""))
            return self.artifact
        if action.type == "brief":
            self.artifact = self._static_result("brief", str(action.value or "research"))
            return self.artifact
        if action.type == "find":
            self.artifact = self._static_result("find", str(action.value or ""))
            return self.artifact
        if action.type == "copy":
            self.clipboard = self.artifact or "暂无可复制内容。"
            return {"copied": True, "length": len(self.clipboard)}
        raise ValueError(f"Unsupported action type: {action.type}")

    def _locator_for(self, target_id: Optional[str]):
        if not target_id or not target_id.startswith("e"):
            raise ValueError(f"Invalid target id: {target_id}")
        element = self._element_for(target_id)
        if not element:
            raise ValueError(f"Target not found in latest observation: {target_id}")
        locator = self._locator_from_element(element)
        if locator:
            return locator
        refreshed = self.observe()
        rematched = self._best_live_match(element, refreshed.elements)
        if rematched:
            locator = self._locator_from_element(rematched)
            if locator:
                return locator
        raise ValueError(f"Could not relocate target reliably: {target_id} ({element.label or element.text or element.selector})")

    def _element_for(self, target_id: str) -> Optional[Element]:
        if not self.last_observation:
            return None
        return next((element for element in self.last_observation.elements if element.id == target_id), None)

    def _locator_from_element(self, element: Element):
        candidates = []
        if element.selector:
            candidates.append(self.page.locator(element.selector))
        if element.label:
            if element.role in {"button", "link"}:
                candidates.append(self.page.get_by_role(element.role, name=element.label))
            candidates.append(self.page.get_by_label(element.label))
        if element.placeholder:
            candidates.append(self.page.get_by_placeholder(element.placeholder))
        if element.href:
            candidates.append(self.page.locator(f'a[href="{element.href}"]'))
        if element.text and element.role in {"button", "link"}:
            candidates.append(self.page.get_by_role(element.role, name=element.text))
        for locator in candidates:
            try:
                resolved = self._best_locator_candidate(locator, element)
                if resolved:
                    return resolved
            except Exception:
                continue
        return None

    def _best_locator_candidate(self, locator: Any, element: Element):
        count = locator.count()
        if count <= 0:
            return None
        if count == 1:
            only = locator.first
            if self._locator_signature_score(only, element) >= 16:
                return only
            return None
        best_index = -1
        best_score = -1
        limit = min(count, 8)
        for index in range(limit):
            candidate = locator.nth(index)
            score = self._locator_signature_score(candidate, element)
            if score > best_score:
                best_score = score
                best_index = index
        if best_index >= 0 and best_score >= 20:
            return locator.nth(best_index)
        return None

    def _locator_signature_score(self, locator: Any, element: Element) -> int:
        try:
            info = locator.evaluate(
                """node => {
                    const textOf = value => String(value || '').replace(/\\s+/g, ' ').trim();
                    const labelFor = new Map(Array.from(document.querySelectorAll('label[for]')).map(label => [label.getAttribute('for'), textOf(label.innerText || label.textContent)]));
                    const nearestLabel = target => {
                        const aria = target.getAttribute('aria-label');
                        if (aria) return textOf(aria);
                        if (target.id && labelFor.has(target.id)) return labelFor.get(target.id);
                        const wrapping = target.closest('label');
                        return wrapping ? textOf(wrapping.innerText || wrapping.textContent) : '';
                    };
                    const sectionLabel = target => {
                        const parent = target.closest('section, article, form, main');
                        if (!parent) return '';
                        const aria = parent.getAttribute('aria-label');
                        if (aria) return textOf(aria);
                        const heading = parent.querySelector('h1,h2,h3');
                        return heading ? textOf(heading.innerText || heading.textContent) : '';
                    };
                    const rect = target.getBoundingClientRect();
                    return {
                        tag: (node.tagName || '').toLowerCase(),
                        role: node.getAttribute('role') || '',
                        type: node.getAttribute('type') || '',
                        name: node.getAttribute('name') || '',
                        label: nearestLabel(node),
                        text: textOf(node.innerText || node.textContent).slice(0, 160),
                        placeholder: node.getAttribute('placeholder') || '',
                        href: node.href || node.getAttribute('href') || '',
                        formId: (node.closest('form') && (node.closest('form').id || node.closest('form').getAttribute('aria-label'))) || '',
                        sectionLabel: sectionLabel(node),
                        visible: !!(rect.width || rect.height),
                        enabled: !node.disabled && node.getAttribute('aria-disabled') !== 'true'
                    };
                }""",
                timeout=2500,
            )
        except Exception:
            return -1
        haystack = " ".join(
            str(info.get(key) or "")
            for key in ["tag", "role", "type", "name", "label", "text", "placeholder", "href", "formId", "sectionLabel"]
        ).lower()
        score = 0
        if info.get("tag") == element.tag:
            score += 4
        if info.get("role") == element.role and element.role:
            score += 5
        if info.get("type") == element.type and element.type:
            score += 4
        for field, weight in [("name", 6), ("label", 10), ("text", 10), ("placeholder", 8), ("href", 12), ("formId", 8), ("sectionLabel", 6)]:
            expected = str(getattr(element, self._element_attr_name(field)) or "").strip().lower()
            actual = str(info.get(field) or "").strip().lower()
            if not expected or not actual:
                continue
            if expected == actual:
                score += weight
            elif expected in actual or actual in expected:
                score += max(3, weight // 2)
        if info.get("visible") == element.visible:
            score += 2
        if info.get("enabled") == element.enabled:
            score += 2
        token_hits = [token for token in self._signature_tokens(element) if token in haystack]
        score += min(len(token_hits), 6)
        return score

    def _element_attr_name(self, field: str) -> str:
        return {
            "formId": "form_id",
            "sectionLabel": "section_label",
        }.get(field, field)

    def _signature_tokens(self, element: Element) -> list[str]:
        values = [
            element.label,
            element.text,
            element.placeholder,
            element.name,
            element.href,
            element.form_id,
            element.section_label,
        ]
        tokens = []
        for value in values:
            for token in str(value or "").lower().replace("/", " ").replace("-", " ").split():
                if len(token) >= 2:
                    tokens.append(token)
        return tokens

    def _best_live_match(self, element: Element, candidates: list[Element]) -> Optional[Element]:
        best: Optional[Element] = None
        best_score = -1
        for candidate in candidates:
            score = self._element_similarity_score(element, candidate)
            if score > best_score:
                best_score = score
                best = candidate
        return best if best and best_score >= 18 else None

    def _element_similarity_score(self, left: Element, right: Element) -> int:
        score = 0
        if left.tag == right.tag:
            score += 4
        if left.role and left.role == right.role:
            score += 4
        if left.type and left.type == right.type:
            score += 3
        for attr, weight in [
            ("name", 5),
            ("label", 8),
            ("text", 8),
            ("placeholder", 6),
            ("href", 10),
            ("form_id", 6),
            ("section_label", 5),
        ]:
            a = str(getattr(left, attr) or "").strip().lower()
            b = str(getattr(right, attr) or "").strip().lower()
            if not a or not b:
                continue
            if a == b:
                score += weight
            elif a in b or b in a:
                score += max(2, weight // 2)
        if left.visible == right.visible:
            score += 1
        if left.enabled == right.enabled:
            score += 1
        return score

    def _highlight_locator(self, locator: Any) -> None:
        try:
            locator.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass
        try:
            locator.evaluate(
                """element => {
                    element.style.outline = '4px solid #f97316';
                    element.style.boxShadow = '0 0 0 8px rgba(249, 115, 22, 0.24)';
                    element.style.borderRadius = element.style.borderRadius || '10px';
                }""",
                timeout=3000,
            )
        except Exception:
            # Highlight is a safety affordance; if the page is in a transient
            # layout state, the agent should still continue and record the step.
            return

    def _click_locator(self, locator: Any) -> None:
        try:
            locator.click(timeout=8000, no_wait_after=True)
            return
        except Exception:
            pass
        try:
            locator.click(timeout=3000, no_wait_after=True, force=True)
            return
        except Exception:
            pass
        locator.evaluate("element => element.click()")

    def _extract(self, keyword: str) -> list[str]:
        from .executor import BrowserHarness

        observation = self.observe()
        return BrowserHarness(observation).extract(keyword)

    def _collect(self, kind: str) -> Dict[str, Any]:
        from .executor import BrowserHarness

        observation = self.observe()
        return BrowserHarness(observation).collect(kind)

    def _static_result(self, action_type: str, value: str = "") -> str:
        from .executor import BrowserHarness

        harness = BrowserHarness(self.observe(), llm_config=self.llm_config, memory=self.memory)
        if action_type == "summarize":
            return harness.summarize()
        if action_type == "compare":
            return harness.compare(value)
        if action_type == "brief":
            return harness.brief(value)
        if action_type == "find":
            return harness.find_on_page(value)
        raise ValueError(action_type)

    def _compare(self, command: str) -> str:
        from .executor import BrowserHarness

        harness = BrowserHarness(self.observe(), llm_config=self.llm_config, memory=self.memory)
        return harness.compare(command)

    def _sample_detail_pages(self, command: str) -> None:
        if not self.memory or not self.page:
            return
        base = self.last_observation or self.observe()
        candidates = select_sampling_candidates(command, base, self.memory, limit=3)
        for candidate in candidates:
            href = str(candidate.get("href") or "").strip()
            if not href:
                continue
            temp_context = None
            temp_page = None
            try:
                temp_context = self.browser.new_context(viewport={"width": 1280, "height": 900}) if self.browser else None
                temp_page = temp_context.new_page() if temp_context else self.page.context.new_page()
                try:
                    temp_page.goto(href, wait_until="commit", timeout=12000)
                except Exception:
                    if not temp_page.url or temp_page.url == "about:blank":
                        raise
                try:
                    temp_page.wait_for_load_state("domcontentloaded", timeout=4000)
                except Exception:
                    pass
                temp_page.wait_for_timeout(1500)
                detail_observation = self._build_observation(temp_page, capture_screenshot=False)
                detail_metadata = self._detail_metadata(temp_page)
                detail_summary = self._detail_summary(detail_observation, detail_metadata)
                self.memory.remember_detail_page(candidate, detail_observation, summary=detail_summary, metadata=detail_metadata)
            except Exception as exc:
                self.memory.notes.append(f"详情页采样失败：{candidate.get('title') or href} -> {exc}")
                self.memory.notes = self.memory.notes[-16:]
                fallback_observation = self._fallback_detail_observation(candidate)
                fallback_metadata = self._fallback_detail_metadata(candidate, exc)
                fallback_summary = self._detail_summary(fallback_observation, fallback_metadata)
                self.memory.remember_detail_page(
                    candidate,
                    fallback_observation,
                    summary=fallback_summary,
                    metadata=fallback_metadata,
                )
            finally:
                if temp_page:
                    temp_page.close()
                if temp_context:
                    temp_context.close()

    def _ensure_page(self) -> None:
        if not self.page:
            self.start()

    def _select_active_page(self, context: Any) -> Any:
        pages = [page for page in context.pages if not page.is_closed()]
        if not pages:
            return context.new_page()
        http_pages = [page for page in pages if (page.url or "").startswith(("http://", "https://", "file://"))]
        return http_pages[-1] if http_pages else pages[-1]

    def _live_elements(self, page: Any) -> list[Element]:
        raw_items = page.evaluate(
            """selector => {
                const nodes = Array.from(document.querySelectorAll(selector));
                const labelFor = new Map(Array.from(document.querySelectorAll('label[for]')).map(label => [label.getAttribute('for'), label.innerText.trim()]));
                const cssEscape = value => {
                    if (window.CSS && CSS.escape) return CSS.escape(value);
                    return String(value).replace(/["\\\\]/g, '\\\\$&');
                };
                const textOf = node => (node.innerText || node.textContent || '').replace(/\\s+/g, ' ').trim();
                const nearestLabel = node => {
                    const aria = node.getAttribute('aria-label');
                    if (aria) return aria.trim();
                    if (node.id && labelFor.has(node.id)) return labelFor.get(node.id);
                    const wrapping = node.closest('label');
                    if (wrapping) return textOf(wrapping);
                    return '';
                };
                const sectionLabel = node => {
                    const parent = node.closest('section, article, form, main');
                    if (!parent) return '';
                    const aria = parent.getAttribute('aria-label');
                    if (aria) return aria.trim();
                    const heading = parent.querySelector('h1,h2,h3');
                    return heading ? textOf(heading) : '';
                };
                const selectorFor = node => {
                    const nthOfType = target => {
                        let count = 0;
                        let sibling = target;
                        while (sibling) {
                            if (sibling.tagName === target.tagName) count += 1;
                            sibling = sibling.previousElementSibling;
                        }
                        return count || 1;
                    };
                    const step = target => {
                        if (target.id) return `#${cssEscape(target.id)}`;
                        const tag = target.tagName.toLowerCase();
                        const attrs = [];
                        if (target.getAttribute('name')) attrs.push(`[name="${String(target.getAttribute('name')).replace(/"/g, '\\\\"')}"]`);
                        if (tag === 'input' && target.getAttribute('type')) attrs.push(`[type="${String(target.getAttribute('type')).replace(/"/g, '\\\\"')}"]`);
                        if (target.getAttribute('aria-label')) attrs.push(`[aria-label="${String(target.getAttribute('aria-label')).replace(/"/g, '\\\\"')}"]`);
                        if (target.getAttribute('href')) attrs.push(`[href="${String(target.getAttribute('href')).replace(/"/g, '\\\\"')}"]`);
                        const base = `${tag}${attrs.join('')}`;
                        const nth = nthOfType(target);
                        if (nth > 1 || attrs.length === 0) return `${base}:nth-of-type(${nth})`;
                        return base;
                    };
                    const parts = [];
                    let current = node;
                    let depth = 0;
                    while (current && current.nodeType === Node.ELEMENT_NODE && depth < 6) {
                        parts.push(step(current));
                        if (current.id) break;
                        current = current.parentElement;
                        depth += 1;
                    }
                    return parts.reverse().join(' > ');
                };
                return nodes.map((node, index) => {
                    const rect = node.getBoundingClientRect();
                    const style = window.getComputedStyle(node);
                    const tag = node.tagName.toLowerCase();
                    const type = node.getAttribute('type') || '';
                    let role = node.getAttribute('role') || '';
                    if (!role) {
                        if (tag === 'a') role = 'link';
                        else if (tag === 'button' || ['button', 'submit', 'reset'].includes(type)) role = 'button';
                        else if (tag === 'textarea') role = 'textbox';
                        else if (tag === 'select') role = 'combobox';
                        else if (tag === 'input' && type === 'search') role = 'searchbox';
                        else if (tag === 'input') role = 'textbox';
                    }
                    const form = node.closest('form');
                    return {
                        id: `e${index + 1}`,
                        tag,
                        selector: selectorFor(node),
                        role,
                        type,
                        name: node.getAttribute('name') || '',
                        label: nearestLabel(node),
                        text: textOf(node).slice(0, 160),
                        placeholder: node.getAttribute('placeholder') || '',
                        href: node.href || node.getAttribute('href') || '',
                        value: 'value' in node ? String(node.value || '') : '',
                        formId: form ? (form.id || form.getAttribute('aria-label') || '') : '',
                        sectionLabel: sectionLabel(node),
                        visible: !!(rect.width || rect.height) && style.visibility !== 'hidden' && style.display !== 'none',
                        enabled: !node.disabled && node.getAttribute('aria-disabled') !== 'true',
                        bbox: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                        contentEditable: node.isContentEditable,
                        clickable: !!node.onclick
                    };
                });
            }""",
            INTERACTIVE_SELECTOR,
        )
        return [
            Element(
                id=str(item.get("id", f"e{index + 1}")),
                tag=str(item.get("tag", "")),
                selector=str(item.get("selector", "")),
                role=str(item.get("role", "")),
                type=str(item.get("type", "")),
                name=str(item.get("name", "")),
                label=str(item.get("label", "")),
                text=str(item.get("text", "")),
                placeholder=str(item.get("placeholder", "")),
                href=str(item.get("href", "")),
                value=str(item.get("value", "")),
                form_id=str(item.get("formId", "")),
                section_label=str(item.get("sectionLabel", "")),
                visible=bool(item.get("visible", True)),
                enabled=bool(item.get("enabled", True)),
                bbox={key: float(value) for key, value in dict(item.get("bbox") or {}).items()},
                content_editable=bool(item.get("contentEditable", False)),
                clickable=bool(item.get("clickable", False)),
            )
            for index, item in enumerate(raw_items or [])
        ]

    def _capture_observation_screenshot(self, page: Any) -> str:
        self.observation_count += 1
        if self.headless and self.connected_over_cdp:
            return ""
        output = Path(self.screenshot_dir) / f"observe-{self.observation_count:03d}.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            page.screenshot(path=str(output), full_page=False, timeout=10000, animations="disabled")
            return str(output)
        except Exception:
            return ""

    def _observation_summary(self, observation: Observation) -> Dict[str, Any]:
        return {
            "url": observation.url,
            "title": observation.title,
            "elementCount": len(observation.elements),
            "screenshotPath": observation.screenshot_path,
        }

    def _wait_after_action(self, before_url: str) -> None:
        if self.page.url != before_url:
            try:
                self.page.wait_for_load_state("domcontentloaded", timeout=8000)
            except Exception:
                pass
            return
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=3000)
        except Exception:
            pass
        if self.page.url == before_url:
            try:
                self.page.wait_for_url(lambda url: url != before_url, timeout=3000)
            except Exception:
                pass
        if self.page.url == before_url:
            try:
                self.page.wait_for_timeout(250)
            except Exception:
                pass

    def _detail_metadata(self, page: Any) -> Dict[str, Any]:
        try:
            return page.evaluate(
                """() => {
                    const clean = value => (value || '').replace(/\\s+/g, ' ').trim();
                    const seen = new Set();
                    const pushUnique = (items, value, min = 8, max = 240) => {
                        const text = clean(value);
                        if (!text || text.length < min || text.length > max || seen.has(text)) return;
                        seen.add(text);
                        items.push(text);
                    };
                    const pickTexts = selectors => {
                        const items = [];
                        for (const selector of selectors) {
                            for (const node of Array.from(document.querySelectorAll(selector)).slice(0, 24)) {
                                pushUnique(items, node.innerText || node.textContent || '');
                            }
                            if (items.length) break;
                        }
                        return items;
                    };
                    const meta = name => {
                        const node = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                        return clean(node ? node.getAttribute('content') : '');
                    };
                    const aboutCandidates = [
                        meta('og:description'),
                        meta('description'),
                        clean(document.querySelector('[data-testid="repository-description"]')?.innerText),
                        clean(document.querySelector('.f4.my-3')?.innerText),
                        clean(document.querySelector('.markdown-body p')?.innerText),
                        clean(document.querySelector('main p')?.innerText),
                    ].filter(Boolean);
                    const capabilitySelectors = [
                        '[data-testid="readme-content"] li',
                        '#readme li',
                        'article.markdown-body li',
                        'article li',
                        'main li',
                    ];
                    const evidenceSelectors = [
                        '[data-testid="readme-content"] p',
                        '#readme p',
                        'article.markdown-body p',
                        'article p',
                        'main p',
                    ];
                    const installLines = [];
                    for (const selector of ['pre code', 'code', '[data-testid="readme-content"] p', '#readme p', 'article.markdown-body p']) {
                        for (const node of Array.from(document.querySelectorAll(selector)).slice(0, 40)) {
                            const text = clean(node.innerText || node.textContent || '');
                            if (/pip install|npm install|pnpm|yarn|playwright install|uv pip|docker|python -m|api key|base url|openai/i.test(text)) {
                                pushUnique(installLines, text, 6, 280);
                            }
                        }
                        if (installLines.length >= 4) break;
                    }
                    const stats = [];
                    const statPairs = [
                        ['stars', 'a[href$="/stargazers"]'],
                        ['forks', 'a[href$="/forks"]'],
                        ['issues', 'a[href*="/issues"]'],
                        ['license', 'a[href*="LICENSE"], a[href*="/license"]'],
                    ];
                    for (const [label, selector] of statPairs) {
                        const node = document.querySelector(selector);
                        const text = clean(node ? node.innerText || node.textContent || '' : '');
                        if (text) pushUnique(stats, `${label}: ${text}`, 3, 120);
                    }
                    return {
                        about: aboutCandidates[0] || '',
                        capabilities: pickTexts(capabilitySelectors).slice(0, 6),
                        install: installLines.slice(0, 4),
                        evidence: pickTexts(evidenceSelectors).slice(0, 5),
                        stats,
                    };
                }"""
            ) or {}
        except Exception:
            return {}

    def _detail_summary(self, observation: Observation, metadata: Dict[str, Any]) -> str:
        parts = []
        about = str(metadata.get("about") or "").strip()
        if about:
            parts.append(about[:220])
        capabilities = metadata.get("capabilities") if isinstance(metadata.get("capabilities"), list) else []
        if capabilities:
            parts.append("能力点：" + "；".join(str(item)[:100] for item in capabilities[:3]))
        install = metadata.get("install") if isinstance(metadata.get("install"), list) else []
        if install:
            parts.append("安装线索：" + "；".join(str(item)[:120] for item in install[:2]))
        stats = metadata.get("stats") if isinstance(metadata.get("stats"), list) else []
        if stats:
            parts.append("项目指标：" + "；".join(str(item)[:60] for item in stats[:3]))
        if not parts:
            parts.append(observation.title)
        return " | ".join(parts)

    def _fallback_detail_observation(self, candidate: Dict[str, Any]) -> Observation:
        title = str(candidate.get("title") or "").strip() or "候选详情页"
        summary = str(candidate.get("summary") or "").strip()
        return Observation(
            url=str(candidate.get("href") or candidate.get("source_url") or "").strip(),
            title=title,
            text=summary,
            elements=[],
            headings=[title],
        )

    def _fallback_detail_metadata(self, candidate: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
        summary = str(candidate.get("summary") or "").strip()
        install = []
        if any(token in summary.lower() for token in ["install", "配置", "api", "playwright", "chrome"]):
            install.append(summary[:200])
        capabilities = []
        for chunk in summary.replace("。", "，").split("，"):
            text = chunk.strip()
            if 6 <= len(text) <= 80 and text not in capabilities:
                capabilities.append(text)
            if len(capabilities) >= 4:
                break
        return {
            "about": f"详情页访问受限，已回退使用候选摘要。原因：{str(exc).splitlines()[0]}",
            "capabilities": capabilities,
            "install": install,
            "evidence": [summary] if summary else [],
        }
