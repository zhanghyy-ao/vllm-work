from __future__ import annotations

import re
from typing import Callable, Dict, Iterable, Optional
from urllib.parse import quote

from .schema import Action, Element, Observation, Plan


DEFAULT_SEARCH_URL = "https://www.bing.com/search?q="


def plan_task(command: str, observation: Observation) -> Plan:
    text = (command or "").strip()
    if not text:
        return Plan("请输入任务指令。", 0.0, [])

    if _is_reply_task(text):
        return _plan_reply(text, observation)
    if _is_github_brief_task(text, observation):
        return _plan_brief("github", "分析当前 GitHub 仓库，提取用途、运行线索和工程风险。")
    if _is_ui_analysis_task(text):
        return _plan_brief("ui", "分析当前界面结构、可用控件、主要工作流和风险按钮。")
    if _is_project_analysis_task(text):
        return _plan_brief("project", "分析当前项目或页面的目标、模块、可复用性和下一步行动。")
    if _is_research_task(text):
        return _plan_brief("research", "整理当前页面或搜索结果，形成研究简报。")
    if _is_docs_task(text, observation):
        return _plan_docs_brief(text)
    if _is_find_task(text):
        return _plan_find(text)
    if _is_summarize_task(text):
        return Plan(
            "总结当前页面可见内容。",
            0.70,
            [
                Action("summarize", value=text, reason="用户希望获得页面摘要。"),
                Action("copy", reason="将摘要复制到剪贴板。"),
            ],
        )
    if _is_form_task(text):
        return _plan_form_fill(text, observation)
    if _is_collect_task(text):
        target, label = _detect_collect_target(text)
        return Plan(
            f"结构化抽取页面中的{label}。",
            0.72,
            [
                Action("collect", value=target, reason=f"用户指令指向“{label}”抽取。"),
                Action("copy", reason="将抽取结果复制到剪贴板。"),
            ],
        )
    if _is_compare_task(text):
        return _plan_compare(text, observation)
    if _is_search_task(text):
        return _plan_search(text, observation)
    return _plan_click_or_extract(text, observation)


def _is_search_task(text: str) -> bool:
    return bool(re.search(r"搜索|查找|寻找|找到|检索|主题|资料|论文|天气|今天|今日|最新|新闻|search|weather", text, re.I))


def _is_form_task(text: str) -> bool:
    return bool(re.search(r"填写|填表|表单|姓名=|邮箱=|电话=|主题=|备注=|name=|email=", text, re.I))


def _is_reply_task(text: str) -> bool:
    return bool(re.search(r"回复|回信|回消息|发送草稿|reply", text, re.I))


def _is_research_task(text: str) -> bool:
    return bool(re.search(r"研究|调研|资料|搜索结果|找资料|找.*内容|research|survey", text, re.I))


def _is_github_brief_task(text: str, observation: Observation) -> bool:
    return bool(re.search(r"github|repo|仓库|代码库|README|开源项目", text, re.I) or re.search(r"github\.com", observation.url, re.I))


def _is_ui_analysis_task(text: str) -> bool:
    return bool(re.search(r"分析.*界面|界面.*分析|页面结构|有哪些按钮|能做什么|UI|可用功能", text, re.I))


def _is_project_analysis_task(text: str) -> bool:
    return bool(re.search(r"分析.*项目|项目.*分析|可复用性|工程价值|工程风险|模块划分|架构分析", text, re.I))


def _is_find_task(text: str) -> bool:
    return bool(re.search(r"帮忙查找|帮我查找|页面中找|在.*中找|定位|find on page", text, re.I))


def _is_docs_task(text: str, observation: Observation) -> bool:
    haystack = f"{observation.url} {observation.title}"
    return bool(re.search(r"文档|教程|安装|配置|API|接口|docs|documentation", text, re.I) or re.search(r"docs|documentation|readme", haystack, re.I))


def _is_summarize_task(text: str) -> bool:
    return bool(re.search(r"总结|摘要|概括|提炼|要点|summari[sz]e", text, re.I))


def _is_collect_task(text: str) -> bool:
    return bool(re.search(r"提取|抽取|收集|导出|抓取|链接|邮箱|价格|数据|结构化|collect|extract", text, re.I))


def _is_compare_task(text: str) -> bool:
    return bool(re.search(r"比较|对比|排序|哪个更好|哪个更适合|推荐|compare|rank", text, re.I))


def _plan_search(command: str, observation: Observation) -> Plan:
    query = _clean_search_query(command)
    if _needs_web_search(command):
        return _plan_web_search(query)
    search_input = _best_element(observation.elements, ["search", "搜索", "查找", "query", "关键词"], _is_text_input)
    submit = _best_element(observation.elements, ["搜索", "查找", "search"], _is_search_submit)
    if search_input:
        actions = [
            Action("type", target_id=search_input.id, value=query, reason=f"找到搜索输入框：{_name(search_input)}。")
        ]
        if submit:
            actions.append(Action("click", target_id=submit.id, reason=f"点击搜索按钮：{_name(submit)}。"))
        else:
            actions.append(Action("press", target_id=search_input.id, key="Enter", reason="页面没有明显搜索按钮，使用 Enter 提交。"))
        actions.append(Action("extract", value=query, reason="搜索后提取页面中与主题相关的内容。"))
        return Plan(f"在当前页面搜索“{query}”。", 0.82, actions)
    return _plan_web_search(query)


def _plan_web_search(query: str) -> Plan:
    return Plan(
        f"当前页面没有搜索框，跳转到搜索引擎搜索“{query}”。",
        0.68,
        [
            Action("navigate", value=DEFAULT_SEARCH_URL + quote(query), reason="未发现页面内搜索框，使用默认搜索引擎。"),
            Action("extract", value=query, reason="打开搜索结果页后提取与主题相关的内容。"),
            Action("copy", reason="将搜索摘要复制到剪贴板。"),
        ],
    )


def _needs_web_search(command: str) -> bool:
    return bool(re.search(r"今天|今日|现在|当前|最新|实时|天气|新闻|汇率|股价|价格|weather|today|latest|current", command, re.I))


def _plan_form_fill(command: str, observation: Observation) -> Plan:
    fields = _parse_fields(command)
    actions = []
    misses = []
    context = _best_form_context(observation.elements, fields.keys())
    for key, value in fields.items():
        target = _best_field_element(observation.elements, key, context)
        if not target:
            misses.append(key)
            continue
        actions.append(Action("type", target_id=target.id, value=value, reason=f"字段“{key}”匹配到“{_name(target)}”。"))
    submit_candidates = _context_elements(observation.elements, context) if context else observation.elements
    submit = _best_element(submit_candidates, ["提交", "保存", "发送", "submit"], _is_clickable)
    if submit:
        actions.append(Action("highlight", target_id=submit.id, reason="提交属于高风险动作，先高亮按钮，等待用户确认。"))
    return Plan(f"填写 {sum(action.type == 'type' for action in actions)} 个字段。", 0.78 if actions else 0.2, actions, [f"未匹配字段：{'、'.join(misses)}"] if misses else [])


def _plan_reply(command: str, observation: Observation) -> Plan:
    value = _clean_reply_text(command)
    input_box = _best_element(observation.elements, ["消息", "回复", "评论", "输入", "reply", "message"], _is_text_input)
    send = _best_element(observation.elements, ["发送", "回复", "send", "提交"], _is_clickable)
    actions = []
    if input_box:
        actions.append(Action("type", target_id=input_box.id, value=value, reason=f"找到消息输入区域：{_name(input_box)}。"))
    if send:
        actions.append(Action("highlight", target_id=send.id, reason="发送消息属于高风险动作，只填草稿并高亮发送按钮。"))
    return Plan("生成回复草稿，不自动发送。", 0.76 if actions else 0.25, actions)


def _plan_brief(kind: str, summary: str) -> Plan:
    return Plan(
        summary,
        0.74,
        [
            Action("brief", value=kind, reason=f"当前任务适合使用 {kind} 真实场景简报。"),
            Action("copy", reason="将简报复制到剪贴板。"),
        ],
    )


def _plan_docs_brief(command: str) -> Plan:
    return Plan(
        "在当前文档页中定位相关内容并生成摘要。",
        0.73,
        [
            Action("extract", value=command, reason="先提取与用户问题相关的文档片段。"),
            Action("brief", value="docs", reason="再按文档站格式整理安装、配置或 API 线索。"),
            Action("copy", reason="将文档摘要复制到剪贴板。"),
        ],
    )


def _plan_find(command: str) -> Plan:
    query = _clean_find_query(command)
    return Plan(
        f"在当前页面查找“{query}”。",
        0.70,
        [
            Action("find", value=query, reason="用户希望在当前页面定位相关内容。"),
            Action("copy", reason="将查找结果复制到剪贴板。"),
        ],
    )


def _plan_compare(command: str, observation: Observation) -> Plan:
    focus = _clean_compare_focus(command)
    search_input = _best_element(observation.elements, ["search", "搜索", "查找", "query", "关键词"], _is_text_input)
    submit = _best_element(observation.elements, ["搜索", "查找", "search"], _is_search_submit)
    current_cards_relevant = len(_matching_cards(observation, focus)) >= 2
    enough_candidates = len(observation.cards) >= 2 or len(observation.tables) >= 1

    if focus and search_input and not current_cards_relevant:
        actions = [
            Action("type", target_id=search_input.id, value=focus, reason=f"先搜索比较主题“{focus}”，补充相关候选。"),
        ]
        if submit:
            actions.append(Action("click", target_id=submit.id, reason=f"点击搜索按钮：{_name(submit)}。"))
        else:
            actions.append(Action("press", target_id=search_input.id, key="Enter", reason="未发现明显搜索按钮，使用 Enter 提交搜索。"))
        actions.extend(
            [
                Action("collect", value="cards", reason="收集搜索后页面中的候选结果，形成结构化上下文。"),
                Action("compare", value=command, reason="结合搜索结果、当前页面和记忆上下文进行综合比较。"),
                Action("copy", reason="将综合比较结果复制到剪贴板。"),
            ]
        )
        return Plan(f"先搜索“{focus}”再比较候选项。", 0.79, actions)

    if focus and not enough_candidates and not search_input:
        return Plan(
            f"当前页面缺少候选项，先用搜索引擎搜索“{focus}”再进行比较。",
            0.7,
            [
                Action("navigate", value=DEFAULT_SEARCH_URL + quote(focus), reason="当前页面缺少足够候选，切换到搜索引擎。"),
                Action("collect", value="cards", reason="收集搜索结果卡片。"),
                Action("compare", value=command, reason="根据搜索结果进行比较。"),
                Action("copy", reason="复制比较结果。"),
            ],
        )

    return Plan(
        "比较页面中的候选项并给出综合推荐。",
        0.72,
        [
            Action("collect", value="cards", reason="先收集当前页面候选项，便于后续结构化比较。"),
            Action("compare", value=command, reason="综合价格、评分、日期、特征和上下文记忆进行比较。"),
            Action("copy", reason="将比较结果复制到剪贴板。"),
        ],
    )


def _plan_click_or_extract(command: str, observation: Observation) -> Plan:
    click_text = re.sub(r"点击|打开|进入", "", command).strip()
    target = _best_click_target(observation.elements, click_text)
    if target:
        return Plan(f"点击“{click_text}”。", 0.65, [Action("click", target_id=target.id, reason=f"找到最接近的可点击元素：{_name(target)}。")])
    return Plan("未识别到明确操作，先提取页面相关内容。", 0.45, [Action("extract", value=command, reason="保底策略：提取相关页面片段。")])


def _clean_search_query(command: str) -> str:
    cleaned = re.sub(r"帮我|请|搜索|查找|寻找|找到|检索|相关主题的内容|相关内容|主题|资料|论文|search", " ", command, flags=re.I)
    cleaned = re.sub(r"[：:]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip() or command.strip()


def _clean_reply_text(command: str) -> str:
    if "：" in command or ":" in command:
        return re.split(r"[：:]", command, maxsplit=1)[1].strip()
    return re.sub(r"回复|回信|回消息|发送草稿|reply", "", command, flags=re.I).strip()


def _clean_compare_focus(command: str) -> str:
    cleaned = re.sub(r"帮我|请|比较|对比|排序|哪个更好|哪个更适合|推荐|这些|方案|产品|工具|compare|rank", " ", command, flags=re.I)
    cleaned = re.sub(r"[：:]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _clean_find_query(command: str) -> str:
    cleaned = re.sub(r"帮忙查找|帮我查找|页面中找|在.*中找|定位|find on page", " ", command, flags=re.I)
    cleaned = re.sub(r"[：:]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip() or command.strip()


def _parse_fields(command: str) -> Dict[str, str]:
    normalized = re.sub(r"请|帮我|填写|填表|表单", " ", command)
    normalized = normalized.replace("，", " ").replace("；", " ")
    pattern = re.compile(r"([\u4e00-\u9fa5A-Za-z_ -]{1,12})\s*=\s*([^=\s]+(?:\s(?![\u4e00-\u9fa5A-Za-z_ -]{1,12}\s*=)[^=\s]+)*)")
    fields = {match.group(1).strip(): match.group(2).strip() for match in pattern.finditer(normalized)}
    if fields:
        return fields
    presets = {
        "姓名": r"姓名[:： ]+([^\s，,]+)",
        "邮箱": r"邮箱[:： ]+([^\s，,]+)",
        "电话": r"电话[:： ]+([^\s，,]+)",
        "主题": r"主题[:： ]+([^\s，,]+)",
        "备注": r"备注[:： ]+(.+)$",
    }
    for key, expr in presets.items():
        found = re.search(expr, command)
        if found:
            fields[key] = found.group(1).strip()
    return fields


def _detect_collect_target(command: str) -> tuple[str, str]:
    if re.search(r"链接|网址|url|link", command, re.I) and re.search(r"邮箱|邮件|email", command, re.I):
        return "contacts", "链接和邮箱"
    if re.search(r"邮箱|邮件|email", command, re.I):
        return "emails", "邮箱"
    if re.search(r"价格|价钱|金额|price", command, re.I):
        return "prices", "价格"
    if re.search(r"链接|网址|url|link", command, re.I):
        return "links", "链接"
    if re.search(r"表格|table", command, re.I):
        return "tables", "表格"
    return "cards", "结果卡片"


def _best_element(elements: Iterable[Element], keywords: list[str], predicate: Callable[[Element], bool]) -> Optional[Element]:
    scored = [(element, _score_element(element, keywords)) for element in elements if predicate(element)]
    scored = [item for item in scored if item[1] > 0]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[0][0] if scored else None


def _best_form_context(elements: Iterable[Element], field_keys: Iterable[str]) -> str:
    keys = [str(key).lower() for key in field_keys if str(key).strip()]
    scores: Dict[str, int] = {}
    for element in elements:
        if not _is_text_input(element):
            continue
        context = _element_context(element)
        if not context:
            continue
        text = element.haystack()
        score = sum(3 for key in keys if key and key in text)
        if re.search(r"表单|form|contact|profile|课程 demo", context, re.I):
            score += 2
        if re.search(r"搜索|search", context, re.I):
            score -= 3
        if score > 0:
            scores[context] = scores.get(context, 0) + score
    return max(scores.items(), key=lambda item: item[1])[0] if scores else ""


def _best_field_element(elements: Iterable[Element], field_key: str, context: str) -> Optional[Element]:
    candidates = [element for element in elements if _is_text_input(element)]
    if context:
        scoped = _context_elements(candidates, context)
        if scoped:
            candidates = scoped
    scored = [(element, _score_field_element(element, field_key, context)) for element in candidates]
    scored = [item for item in scored if item[1] > 0]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[0][0] if scored else None


def _score_field_element(element: Element, field_key: str, context: str) -> int:
    key = str(field_key or "").lower()
    exact_parts = [element.label.lower(), element.name.lower(), element.placeholder.lower()]
    score = 0
    if key in exact_parts:
        score += 40
    elif any(part and (key in part or part in key) for part in exact_parts):
        score += 20
    if key and key in element.haystack():
        score += 10
    if context and _element_context(element) == context:
        score += 8
    if re.search(r"搜索|search", _element_context(element), re.I) and not re.search(r"搜索|search", key, re.I):
        score -= 20
    return score


def _context_elements(elements: Iterable[Element], context: str) -> list[Element]:
    return [element for element in elements if _element_context(element) == context]


def _element_context(element: Element) -> str:
    return element.form_id or element.section_label


def _best_click_target(elements: Iterable[Element], text: str) -> Optional[Element]:
    wanted = re.sub(r"\s+", " ", text or "").strip().lower()
    clickables = [element for element in elements if _is_clickable(element)]
    exact = [
        element
        for element in clickables
        if wanted
        and wanted in {
            (element.label or "").lower(),
            (element.text or "").lower(),
            (element.name or "").lower(),
        }
    ]
    if exact:
        return exact[0]
    contains = [
        element
        for element in clickables
        if wanted and ((element.label or element.text or element.href or "").lower().find(wanted) >= 0)
    ]
    if contains:
        return contains[0]
    tokens = [token for token in re.split(r"\s+", wanted) if len(token) >= 3]
    scored = []
    for element in clickables:
        haystack = element.haystack()
        score = sum(10 for token in tokens if token in haystack)
        if element.href and score:
            score += 4
        if score:
            scored.append((element, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[0][0] if scored else None


def _matching_cards(observation: Observation, focus: str) -> list[dict]:
    tokens = _focus_tokens(focus)
    if not tokens:
        return observation.cards
    matched = []
    for card in observation.cards:
        text = f"{card.get('title', '')} {card.get('summary', '')}".lower()
        if sum(1 for token in tokens if token in text) > 0:
            matched.append(card)
    return matched


def _focus_tokens(text: str) -> list[str]:
    stopwords = {"和", "与", "及", "或", "the", "a", "an", "vs", "and", "or"}
    tokens = []
    for token in re.split(r"\s+", text.lower()):
        cleaned = token.strip()
        if not cleaned or cleaned in stopwords:
            continue
        if len(cleaned) == 1 and not cleaned.isdigit():
            continue
        tokens.append(cleaned)
    return tokens


def _score_element(element: Element, keywords: list[str]) -> int:
    haystack = element.haystack()
    score = 0
    for keyword in keywords:
        key = str(keyword or "").lower()
        if not key:
            continue
        if key in haystack:
            score += 10
        token_hits = [token for token in re.split(r"[\s/_-]+", key) if len(token) >= 2]
        if token_hits and all(token in haystack for token in token_hits):
            score += 6
    return score


def _is_text_input(element: Element) -> bool:
    return element.tag in {"input", "textarea"} or element.content_editable or element.role in {"textbox", "searchbox", "combobox"}


def _is_clickable(element: Element) -> bool:
    return element.tag in {"button", "a", "select"} or element.role in {"button", "link", "menuitem", "option"} or element.clickable


def _is_search_submit(element: Element) -> bool:
    if not _is_clickable(element):
        return False
    haystack = element.haystack()
    if not re.search(r"搜索|查找|search|query", haystack, re.I):
        return False
    return not re.search(r"提交表单|发送消息|付款|支付|删除|上传|发布|submit form|send message|pay|delete|upload|publish", haystack, re.I)


def _name(element: Element) -> str:
    return element.label or element.placeholder or element.text or element.name or element.id
