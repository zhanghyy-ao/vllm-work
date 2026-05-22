from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable, List, Tuple

from .schema import Action, Observation, Plan


ALLOWED_ACTION_TYPES = {
    "highlight",
    "click",
    "type",
    "press",
    "scroll",
    "navigate",
    "extract",
    "summarize",
    "collect",
    "compare",
    "brief",
    "find",
    "copy",
    "wait",
}

# Generic high-risk verbs. These are blocked unless explicitly allowed.
HIGH_RISK_PATTERN = re.compile(
    r"提交|发送|删除|付款|支付|发布|上传|下单|购买|确认|submit|send|delete|pay|purchase|publish|upload|checkout|confirm",
    re.I,
)

# Hard-risk actions are always blocked or converted, even with explicit submit enabled.
HARD_RISK_PATTERN = re.compile(
    r"删除|付款|支付|上传|下单|购买|结账|密码|验证码|授权|delete|pay|purchase|upload|checkout|password|captcha|otp|permission",
    re.I,
)


def sanitize_plan(plan: Plan, observation: Observation, allow_explicit_submit: bool = False) -> Plan:
    """Validate action schema, drop invalid targets, and apply risk guardrails."""
    valid_ids = {element.id for element in observation.elements}
    actions: List[Action] = []
    warnings = list(plan.warnings)

    for action in plan.actions[:12]:
        if action.type not in ALLOWED_ACTION_TYPES:
            warnings.append(f"已丢弃非法动作类型：{action.type}")
            continue
        if action.target_id and action.target_id not in valid_ids:
            warnings.append(f"已丢弃不存在的 targetId：{action.target_id}")
            continue

        checked, action_warnings = guard_action(action, observation, allow_explicit_submit=allow_explicit_submit)
        warnings.extend(action_warnings)
        actions.append(checked)

    return Plan(
        summary=plan.summary,
        confidence=plan.confidence,
        warnings=warnings,
        actions=actions,
    )


def guard_action(action: Action, observation: Observation, allow_explicit_submit: bool = False) -> Tuple[Action, List[str]]:
    """Convert risky click/press actions into safe highlight actions when needed."""
    target_text = _target_haystack(action, observation)
    action_text = f"{action.type} {action.value or ''} {action.reason} {target_text}"
    if (
        action.type in {"click", "press"}
        and HIGH_RISK_PATTERN.search(action_text)
        and not _is_search_submission(action_text, target_text)
        and not _is_allowed_explicit_submit(action_text, allow_explicit_submit)
    ):
        guarded = replace(
            action,
            type="highlight",
            risk_level="high",
            requires_confirmation=True,
            reason=f"安全拦截：原动作可能触发提交/发送/支付/删除等高风险操作。原原因：{action.reason}",
        )
        return guarded, [f"高风险动作已转为 highlight：{target_text or action.reason}"]

    risk_level = (
        "medium"
        if HIGH_RISK_PATTERN.search(action_text)
        and not _is_search_submission(action_text, target_text)
        and not _is_allowed_explicit_submit(action_text, allow_explicit_submit)
        else action.risk_level
    )
    return replace(action, risk_level=risk_level), []


def _is_allowed_explicit_submit(action_text: str, allow_explicit_submit: bool) -> bool:
    if not allow_explicit_submit:
        return False
    if HARD_RISK_PATTERN.search(action_text):
        return False
    return bool(re.search(r"提交|发送|发布|submit|send|publish", action_text, re.I))


def _is_search_submission(action_text: str, target_text: str) -> bool:
    text = f"{action_text} {target_text}"
    if not re.search(r"搜索|查找|search|query", text, re.I):
        return False
    return not re.search(
        r"提交表单|发送消息|付款|支付|删除|上传|发布|下单|购买|submit form|send message|pay|delete|upload|publish|checkout|purchase",
        text,
        re.I,
    )


def _target_haystack(action: Action, observation: Observation) -> str:
    if not action.target_id:
        return ""
    for element in observation.elements:
        if element.id == action.target_id:
            return element.haystack()
    return ""


def is_high_risk_action(action: Action, observation: Observation) -> bool:
    return bool(HIGH_RISK_PATTERN.search(f"{action.type} {action.value or ''} {action.reason} {_target_haystack(action, observation)}"))


def valid_action_types() -> Iterable[str]:
    return sorted(ALLOWED_ACTION_TYPES)
