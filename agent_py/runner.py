from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .browser_runtime import PlaywrightBrowserRuntime
from .llm_planner import LLMConfig, try_plan_with_llm
from .memory import AgentMemory
from .planner import plan_task
from .safety import sanitize_plan
from .schema import ActionResult, ExecutionResult, Observation, Plan
from .schema import Action


@dataclass
class AgentRunResult:
    task: str
    url: str
    plan: Plan
    execution: ExecutionResult
    planner_source: str
    browser_mode: str = "temporary"
    connection_status: str = ""
    warnings: List[str] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "url": self.url,
            "plannerSource": self.planner_source,
            "browserMode": self.browser_mode,
            "connectionStatus": self.connection_status,
            "warnings": self.warnings,
            "memory": self.memory,
            "plan": self.plan.to_dict(),
            "execution": self.execution.to_dict(),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }


class BrowserAgentRunner:
    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        headless: bool = False,
        max_steps: int = 8,
        cdp_url: str = "",
        slow_mo: int = 0,
        linger_seconds: float = 0,
        screenshot_dir: str = "runs/screenshots",
        allow_explicit_submit: bool = False,
    ) -> None:
        self.llm_config = llm_config
        self.headless = headless
        self.max_steps = max_steps
        self.cdp_url = cdp_url
        self.slow_mo = slow_mo
        self.linger_seconds = linger_seconds
        self.screenshot_dir = screenshot_dir
        self.allow_explicit_submit = allow_explicit_submit

    def run(self, url: str, task: str) -> AgentRunResult:
        with PlaywrightBrowserRuntime(
            headless=self.headless,
            cdp_url=self.cdp_url,
            slow_mo=self.slow_mo,
            screenshot_dir=self.screenshot_dir,
            llm_config=self.llm_config,
            memory=AgentMemory(task=task),
        ) as runtime:
            observation = runtime.goto(url)
            plan, source, warnings = self._plan(task, observation)
            if runtime.connection_error:
                warnings.append(f"CDP connection failed, fell back to temporary Chromium: {runtime.connection_error}")
            if self.max_steps > 0 and len(plan.actions) > self.max_steps:
                plan = Plan(
                    summary=plan.summary,
                    confidence=plan.confidence,
                    warnings=[*plan.warnings, f"动作数超过 max_steps={self.max_steps}，已截断。"],
                    actions=plan.actions[: self.max_steps],
                )
            execution, execution_warnings = self._execute_with_replanning(runtime, task, plan)
            warnings.extend(execution_warnings)
            if self.linger_seconds > 0 and runtime.page:
                runtime.page.wait_for_timeout(int(self.linger_seconds * 1000))
            browser_mode = "cdp-attached" if runtime.connected_over_cdp else "temporary-playwright"
            return AgentRunResult(
                task=task,
                url=execution.url or url,
                plan=plan,
                execution=execution,
                planner_source=source,
                browser_mode=browser_mode,
                connection_status="connected to Chrome CDP" if runtime.connected_over_cdp else "using temporary Chromium",
                warnings=warnings,
                memory=runtime.memory.to_dict() if runtime.memory else {},
            )

    def _plan(self, task: str, observation: Observation) -> tuple[Plan, str, List[str]]:
        warnings: List[str] = []
        try:
            llm_plan = try_plan_with_llm(
                task,
                observation,
                self.llm_config,
                allow_explicit_submit=self.allow_explicit_submit,
            )
            if llm_plan:
                return self._complete_plan(task, sanitize_plan(llm_plan, observation, allow_explicit_submit=self.allow_explicit_submit)), "llm", warnings
        except Exception as exc:
            warnings.append(f"LLM Planner failed, falling back to rule planner: {exc}")

        return self._complete_plan(task, sanitize_plan(plan_task(task, observation), observation, allow_explicit_submit=self.allow_explicit_submit)), "rule", warnings

    def _execute_with_replanning(
        self,
        runtime: PlaywrightBrowserRuntime,
        task: str,
        plan: Plan,
    ) -> tuple[ExecutionResult, List[str]]:
        warnings: List[str] = []
        logs: List[ActionResult] = []
        trajectory: List[Dict[str, Any]] = []
        pending = list(plan.actions)
        steps = 0
        replans = 0
        max_steps = max(self.max_steps, 1)

        while pending and steps < max_steps:
            action = pending.pop(0)
            steps += 1
            try:
                output = runtime.execute(action)
                observation = runtime.observe()
                if runtime.memory:
                    runtime.memory.remember(action, observation, output=output, artifact=runtime.artifact)
                result = ActionResult(action=action, ok=True, output=output, url=observation.url, artifact=runtime.artifact)
                logs.append(result)
                entry = result.to_dict()
                entry["observation"] = _observation_summary(observation)
                trajectory.append(entry)
            except Exception as exc:
                url = runtime.page.url if runtime.page else ""
                result = ActionResult(action=action, ok=False, error=str(exc), url=url, artifact=runtime.artifact)
                entry = result.to_dict()
                entry["fallbackReason"] = "action_failed"
                trajectory.append(entry)

                if replans >= 2 or steps >= max_steps:
                    logs.append(result)
                    break

                try:
                    observation = runtime.observe()
                    fallback = self._complete_plan(
                        task,
                        sanitize_plan(
                            plan_task(task, observation),
                            observation,
                            allow_explicit_submit=self.allow_explicit_submit,
                        ),
                    )
                    if not fallback.actions:
                        break
                    replans += 1
                    pending = fallback.actions
                    warnings.append(
                        f"动作失败后已基于最新页面重新规划第 {replans} 次：{action.type} {action.target_id or ''} -> {exc}"
                    )
                    trajectory[-1]["replan"] = fallback.to_dict()
                    trajectory[-1]["observation"] = _observation_summary(observation)
                    continue
                except Exception as replan_exc:
                    warnings.append(f"动作失败后重规划也失败：{replan_exc}")
                    logs.append(result)
                    break

        if steps >= max_steps and pending:
            warnings.append(f"执行达到 max_steps={max_steps}，仍有 {len(pending)} 个动作未执行。")

        if _needs_artifact(task) and not runtime.artifact and steps < max_steps:
            for action in [Action("summarize", value=task, reason="执行结束后补充页面摘要作为最终产物。"), Action("copy", reason="复制最终产物。")]:
                if steps >= max_steps:
                    break
                steps += 1
                try:
                    output = runtime.execute(action)
                    observation = runtime.observe()
                    if runtime.memory:
                        runtime.memory.remember(action, observation, output=output, artifact=runtime.artifact)
                    result = ActionResult(action=action, ok=True, output=output, url=observation.url, artifact=runtime.artifact)
                    logs.append(result)
                    entry = result.to_dict()
                    entry["observation"] = _observation_summary(observation)
                    entry["autoSupplement"] = True
                    trajectory.append(entry)
                except Exception as exc:
                    result = ActionResult(
                        action=action,
                        ok=False,
                        error=str(exc),
                        url=runtime.page.url if runtime.page else "",
                        artifact=runtime.artifact,
                    )
                    logs.append(result)
                    trajectory.append(result.to_dict())
                    break

        return ExecutionResult(
            url=runtime.page.url if runtime.page else "",
            logs=logs,
            artifact=runtime.artifact,
            trajectory=trajectory,
        ), warnings

    def _complete_plan(self, task: str, plan: Plan) -> Plan:
        if _looks_like_search_task(task):
            has_browser_action = any(action.type in {"click", "press", "navigate"} for action in plan.actions)
            has_result_action = _has_result_action(plan)
            if has_browser_action and not has_result_action:
                query = _query_from_plan(task, plan)
                return Plan(
                    summary=plan.summary,
                    confidence=plan.confidence,
                    warnings=plan.warnings,
                    actions=[
                        *plan.actions,
                        Action("extract", value=query, reason="搜索动作完成后提取结果摘要，保证任务闭环。"),
                        Action("copy", reason="将搜索摘要复制到剪贴板。"),
                    ],
                )
            return plan
        if _needs_artifact(task) and not _has_result_action(plan):
            return Plan(
                summary=plan.summary,
                confidence=plan.confidence,
                warnings=plan.warnings,
                actions=[
                    *plan.actions,
                    Action("summarize", value=task, reason="补充最终页面摘要，保证任务有可展示结果。"),
                    Action("copy", reason="将最终结果复制到剪贴板。"),
                ],
            )
        return plan


def _looks_like_search_task(task: str) -> bool:
    return bool(re.search(r"搜索|查找|寻找|找到|检索|资料|论文|天气|今天|今日|最新|新闻|search|weather", task, re.I))


def _needs_artifact(task: str) -> bool:
    return bool(
        re.search(
            r"搜索|查找|寻找|找到|检索|资料|论文|天气|今天|今日|最新|新闻|分析|总结|打开|填写|回复|比较|提取|抽取|search|weather|open|fill|reply|compare|extract",
            task,
            re.I,
        )
    )


def _has_result_action(plan: Plan) -> bool:
    return any(action.type in {"extract", "summarize", "collect", "compare", "brief", "find"} for action in plan.actions)


def _query_from_plan(task: str, plan: Plan) -> str:
    for action in plan.actions:
        if action.type == "type" and action.value:
            return str(action.value)
    cleaned = re.sub(r"帮我|请|搜索|查找|寻找|找到|检索|相关主题的内容|相关内容|资料|论文|search", " ", task, flags=re.I)
    cleaned = re.sub(r"[：:]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip() or task.strip()


def _observation_summary(observation: Observation) -> Dict[str, Any]:
    return {
        "url": observation.url,
        "title": observation.title,
        "elementCount": len(observation.elements),
        "screenshotPath": observation.screenshot_path,
        "viewport": observation.viewport,
    }


def save_trajectory(result: AgentRunResult, path: str) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(output)
