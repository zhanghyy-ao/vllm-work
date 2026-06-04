from __future__ import annotations

import uuid
from typing import Iterable, List

from browser_agent.types import Observation, Plan, ScenarioDefinition, WorkflowSpec, action_from_spec


SCENARIOS: List[ScenarioDefinition] = [
    ScenarioDefinition(
        name="comparison_recommendation",
        summary="\u63a8\u8350\u4efb\u52a1\u6d41\u7a0b",
        confidence=0.75,
        keywords=[
            "\u6bd4\u8f83",
            "\u63a8\u8350",
            "\u54ea\u6b3e",
            "\u5bf9\u6bd4",
            "\u9009\u54ea\u4e2a",
            "compare",
            "recommend",
        ],
        action_specs=[
            {"tool": "search", "reason": "\u5148\u641c\u96c6\u5019\u9009", "value": "goal"},
            {"tool": "collect", "reason": "\u6536\u96c6\u5019\u9009\u5361\u7247", "value": "cards"},
            {"tool": "open_topk", "reason": "\u6253\u5f00\u524d3\u4e2a\u8be6\u60c5\u9875\u91c7\u6837", "value": "3"},
            {"tool": "compare", "reason": "\u591a\u7ef4\u6bd4\u8f83\u5e76\u63a8\u8350", "value": "goal"},
        ],
        risk_level="low",
        deliverable="comparison_table",
        success_checks=[
            "at_least_three_candidates",
            "clear_recommendation",
            "evidence_summary_present",
        ],
    ),
    ScenarioDefinition(
        name="form_filling",
        summary="\u8868\u5355\u4efb\u52a1\u6d41\u7a0b",
        confidence=0.72,
        keywords=[
            "\u586b",
            "\u8868\u5355",
            "\u62a5\u540d",
            "\u7533\u8bf7",
            "\u5f55\u5165",
            "form",
            "register",
        ],
        action_specs=[
            {"tool": "analyze_form", "reason": "\u8bc6\u522b\u8868\u5355\u5b57\u6bb5"},
            {"tool": "fill_form", "reason": "\u586b\u5199\u8349\u7a3f"},
            {"tool": "verify", "reason": "\u6821\u9a8c\u586b\u5199\u72b6\u6001"},
        ],
        risk_level="medium",
        deliverable="draft_form_payload",
        success_checks=[
            "required_fields_identified",
            "draft_values_present",
            "verification_passed",
        ],
    ),
    ScenarioDefinition(
        name="booking_reservation",
        summary="\u9884\u8ba2\u4efb\u52a1\u6d41\u7a0b",
        confidence=0.78,
        keywords=[
            "\u9884\u8ba2",
            "\u9884\u7ea6",
            "\u8ba2\u7968",
            "\u8ba2\u4f4d",
            "\u8ba2\u9152\u5e97",
            "\u884c\u7a0b",
            "book",
            "reserve",
        ],
        action_specs=[
            {"tool": "search", "reason": "\u641c\u7d22\u53ef\u9884\u8ba2\u8d44\u6e90", "value": "goal"},
            {"tool": "find_slots", "reason": "\u67e5\u627e\u53ef\u7528\u65f6\u95f4\u6216\u623f\u578b"},
            {"tool": "apply_filters", "reason": "\u6309\u9884\u7b97\u548c\u504f\u597d\u7b5b\u9009", "value": "goal"},
            {"tool": "reserve", "reason": "\u751f\u6210\u5f85\u786e\u8ba4\u9884\u8ba2\u8349\u7a3f"},
        ],
        risk_level="high",
        deliverable="reservation_draft",
        approval_actions=["reserve"],
        success_checks=[
            "candidate_inventory_found",
            "filters_applied",
            "user_confirmation_before_commit",
        ],
    ),
    ScenarioDefinition(
        name="lead_collection",
        summary="\u7ebf\u7d22\u91c7\u96c6\u6d41\u7a0b",
        confidence=0.74,
        keywords=[
            "\u7ebf\u7d22",
            "\u5ba2\u6237\u540d\u5355",
            "\u8054\u7cfb\u4eba",
            "\u90ae\u7bb1",
            "\u83b7\u5ba2",
            "\u9500\u552e\u540d\u5355",
            "lead",
            "prospect",
        ],
        action_specs=[
            {"tool": "search", "reason": "\u68c0\u7d22\u76ee\u6807\u516c\u53f8\u548c\u8054\u7cfb\u4eba", "value": "goal"},
            {"tool": "extract_leads", "reason": "\u62bd\u53d6\u7ed3\u6784\u5316\u7ebf\u7d22"},
            {"tool": "export_csv", "reason": "\u5bfc\u51fa\u4e3a\u53ef\u590d\u7528\u8868\u683c"},
            {"tool": "verify", "reason": "\u68c0\u67e5\u5b57\u6bb5\u5b8c\u6574\u6027"},
        ],
        risk_level="medium",
        deliverable="lead_sheet",
        success_checks=[
            "structured_fields_extracted",
            "exportable_rows_present",
            "integrity_check_passed",
        ],
    ),
    ScenarioDefinition(
        name="monitoring_alerts",
        summary="\u76d1\u63a7\u4efb\u52a1\u6d41\u7a0b",
        confidence=0.76,
        keywords=[
            "\u76d1\u63a7",
            "\u5de1\u68c0",
            "\u4ef7\u683c\u63d0\u9192",
            "\u5e93\u5b58\u63d0\u9192",
            "\u544a\u8b66",
            "\u5173\u6ce8\u53d8\u5316",
            "monitor",
            "alert",
        ],
        action_specs=[
            {"tool": "search", "reason": "\u5b9a\u4f4d\u76d1\u63a7\u76ee\u6807\u9875\u9762", "value": "goal"},
            {"tool": "snapshot_page", "reason": "\u8bb0\u5f55\u5f53\u524d\u57fa\u7ebf"},
            {"tool": "track_price", "reason": "\u767b\u8bb0\u9700\u8981\u76d1\u63a7\u7684\u5173\u952e\u5b57\u6bb5", "value": "goal"},
            {"tool": "set_alert", "reason": "\u914d\u7f6e\u63d0\u9192\u89c4\u5219"},
        ],
        risk_level="low",
        deliverable="alert_rule",
        success_checks=[
            "baseline_captured",
            "watch_target_registered",
            "alert_rule_configured",
        ],
    ),
    ScenarioDefinition(
        name="qa_regression",
        summary="\u6d4b\u8bd5\u4efb\u52a1\u6d41\u7a0b",
        confidence=0.80,
        keywords=[
            "\u6d4b\u8bd5",
            "\u56de\u5f52",
            "\u68c0\u67e5\u9875\u9762",
            "\u68c0\u67e5\u6309\u94ae",
            "\u9a8c\u6536",
            "\u767b\u5f55\u6d41\u7a0b",
            "qa",
            "regression",
        ],
        action_specs=[
            {"tool": "search", "reason": "\u5b9a\u4f4d\u9700\u8981\u9a8c\u8bc1\u7684\u9875\u9762", "value": "goal"},
            {"tool": "snapshot_page", "reason": "\u8bb0\u5f55\u5f53\u524d\u9875\u9762\u72b6\u6001"},
            {"tool": "assert_ui", "reason": "\u6821\u9a8c\u5173\u952e\u6309\u94ae\u4e0e\u6d41\u7a0b"},
            {"tool": "report_bug", "reason": "\u8f93\u51fa\u56de\u5f52\u68c0\u67e5\u62a5\u544a"},
        ],
        risk_level="low",
        deliverable="qa_report",
        success_checks=[
            "baseline_snapshot_present",
            "ui_assertions_passed",
            "report_ready",
        ],
    ),
    ScenarioDefinition(
        name="research",
        summary="\u7814\u7a76\u4efb\u52a1\u6d41\u7a0b",
        confidence=0.68,
        keywords=[],
        action_specs=[
            {"tool": "search", "reason": "\u68c0\u7d22\u76f8\u5173\u9875\u9762", "value": "goal"},
            {"tool": "summarize", "reason": "\u603b\u7ed3\u5173\u952e\u4fe1\u606f"},
        ],
        risk_level="low",
        deliverable="research_summary",
        success_checks=[
            "relevant_pages_found",
            "concise_summary_present",
        ],
    ),
]


def _matches(goal: str, keywords: Iterable[str]) -> bool:
    return any(keyword.lower() in goal.lower() for keyword in keywords)


def _materialize_value(raw_value: str, goal: str) -> str:
    return goal if raw_value == "goal" else raw_value


def _build_plan(goal: str, scenario: ScenarioDefinition) -> Plan:
    actions = []
    for spec in scenario.action_specs:
        spec_copy = dict(spec)
        spec_copy["value"] = _materialize_value(spec_copy.get("value", ""), goal)
        actions.append(action_from_spec(spec_copy, approval_actions=scenario.approval_actions))
    return Plan(
        summary=scenario.summary,
        actions=actions,
        confidence=scenario.confidence,
        scenario=scenario.name,
        risk_level=scenario.risk_level,
        deliverable=scenario.deliverable,
        success_checks=list(scenario.success_checks),
    )


def get_scenario_definition(name: str) -> ScenarioDefinition:
    for scenario in SCENARIOS:
        if scenario.name == name:
            return scenario
    raise KeyError(f"Unknown scenario: {name}")




def detect_domain(goal: str, requested_domain: str = "auto") -> str:
    if requested_domain != "auto":
        return requested_domain
    text = goal.lower()
    if any(token in text for token in ["表单", "报名", "申请", "填写", "问卷", "form", "register", "signup", "apply"]):
        return "form"
    if any(token in text for token in ["预订", "预约", "订票", "订位", "酒店", "餐厅", "book", "reserve", "booking"]):
        return "booking"
    if any(token in text for token in ["线索", "客户名单", "联系人", "邮箱", "获客", "prospect", "lead", "contact list"]):
        return "lead"
    if any(token in text for token in ["监控", "巡检", "价格提醒", "库存提醒", "告警", "monitor", "alert", "watch"]):
        return "monitoring"
    if any(token in text for token in ["测试", "回归", "检查按钮", "验收", "qa", "regression", "测试页面"]):
        return "qa"
    if any(token in text for token in ["github", "repo", "repository", "代码", "开源", "项目"]):
        return "github"
    if any(token in text for token in ["paper", "arxiv", "论文", "scholar", "文献"]):
        return "paper"
    if any(token in text for token in ["购物", "商品", "价格", "键盘", "耳机", "推荐买"]):
        return "shopping"
    if any(token in text for token in ["视频", "b站", "bilibili", "youtube", "字幕", "关键帧", "课程", "学习路线", "内容整理"]):
        return "video"
    return "general"



def plan_workflow_goal(goal: str, observation: Observation, domain: str = "auto") -> WorkflowSpec:
    """Build a workflow shell for the observation-driven agent loop.

    Research workflows intentionally start without fixed action nodes. Evidence
    stages live in `default_search_plan()` and are used as a checklist by the
    dynamic agent loop. Executed nodes are appended at runtime.
    """
    _ = observation
    resolved_domain = detect_domain(goal, domain)
    template = f"{resolved_domain}_research" if resolved_domain in {"github", "paper"} else f"{resolved_domain}_workflow"
    return WorkflowSpec(
        workflow_id=str(uuid.uuid4()),
        template=template,
        goal=goal.strip(),
        domain=resolved_domain,
        summary=f"{resolved_domain} workflow for: {goal.strip()}",
        nodes=[],
        confidence=0.78 if resolved_domain in {"github", "paper"} else 0.68,
        output_schema={
            "summary": "str",
            "candidates": "list",
            "recommendations": "list",
            "decision_criteria": "list",
            "comparison_matrix": "list",
            "video_digest": "dict",
            "multimodal_notes": "list",
            "uncertainties": "list",
            "next_actions": "list",
        },
    )

def plan_scenario_goal(goal: str, observation: Observation) -> Plan:
    """Deterministic scenario routing for harness-safe browser task classes."""
    _ = observation
    text = goal.strip()

    for scenario in SCENARIOS:
        if scenario.keywords and _matches(text, scenario.keywords):
            return _build_plan(text, scenario)

    return _build_plan(text, SCENARIOS[-1])


def plan_goal(goal: str, observation: Observation, domain: str | None = None):
    """Route to either the full browser workflow or the deterministic scenario plan.

    Passing `domain` keeps the newer LLM/browser workflow behavior. Omitting it
    preserves the scenario-harness API used by the market comparison tests.
    """
    if domain is None:
        return plan_scenario_goal(goal, observation)
    return plan_workflow_goal(goal, observation, domain=domain)
