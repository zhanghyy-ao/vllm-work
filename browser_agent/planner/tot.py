from __future__ import annotations

from browser_agent.types import Action, Observation, Plan


def plan_goal(goal: str, observation: Observation) -> Plan:
    """Minimal ToT-style decomposition baseline.

    This is deterministic by design for stable harness behavior.
    """
    text = goal.strip()
    if "比较" in text or "推荐" in text:
        actions = [
            Action(tool="search", reason="先搜集候选", value=text),
            Action(tool="collect", reason="收集候选卡片", value="cards"),
            Action(tool="open_topk", reason="打开前3个详情页采样", value="3"),
            Action(tool="compare", reason="多维比较并推荐", value=text),
        ]
        return Plan(summary="推荐任务流程", actions=actions, confidence=0.75)
    if "填" in text or "表单" in text:
        actions = [
            Action(tool="analyze_form", reason="识别表单字段"),
            Action(tool="fill_form", reason="填写草稿"),
            Action(tool="verify", reason="校验填写状态"),
        ]
        return Plan(summary="表单任务流程", actions=actions, confidence=0.72)
    actions = [
        Action(tool="search", reason="检索相关页面", value=text),
        Action(tool="summarize", reason="总结关键信息"),
    ]
    return Plan(summary="研究任务流程", actions=actions, confidence=0.68)
