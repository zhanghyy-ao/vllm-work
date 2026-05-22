from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from .memory import AgentMemory
from .schema import Observation, Plan

DEFAULT_SEARCH_URL = "https://www.bing.com/search?q="
PHASES = [
    "observe_ui",
    "understand_user_intent",
    "decompose_task",
    "plan_execution",
    "execute_browser_actions",
    "verify_and_finalize",
]


@dataclass
class WorkflowTask:
    task_id: str
    phase: str
    title: str
    goal: str
    status: str = "pending"
    parent_task_id: str = ""
    worker_id: str = ""
    execution_mode: str = "serial"
    target_url: str = ""
    depends_on: List[str] = field(default_factory=list)
    merge_key: str = ""
    completion_criteria: str = ""
    result_summary: str = ""
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "taskId": self.task_id,
            "phase": self.phase,
            "title": self.title,
            "goal": self.goal,
            "status": self.status,
            "parentTaskId": self.parent_task_id,
            "workerId": self.worker_id,
            "executionMode": self.execution_mode,
            "targetUrl": self.target_url,
            "dependsOn": self.depends_on,
            "mergeKey": self.merge_key,
            "completionCriteria": self.completion_criteria,
            "resultSummary": self.result_summary,
            "reasoning": self.reasoning,
        }


@dataclass
class WorkerState:
    worker_id: str
    branch_id: str
    status: str
    assigned_url: str = ""
    latest_reasoning: str = ""
    result_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workerId": self.worker_id,
            "branchId": self.branch_id,
            "status": self.status,
            "assignedUrl": self.assigned_url,
            "latestReasoning": self.latest_reasoning,
            "resultSummary": self.result_summary,
        }


@dataclass
class BranchResult:
    branch_id: str
    worker_id: str
    status: str
    target_url: str = ""
    summary: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branchId": self.branch_id,
            "workerId": self.worker_id,
            "status": self.status,
            "targetUrl": self.target_url,
            "summary": self.summary,
            "data": self.data,
        }


@dataclass
class MemoryMergeRecord:
    branch_id: str
    worker_id: str
    merged_keys: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branchId": self.branch_id,
            "workerId": self.worker_id,
            "mergedKeys": self.merged_keys,
            "note": self.note,
        }


@dataclass
class ControllerResult:
    planner_source: str
    current_phase: str
    phase_reasoning: str
    task_queue: List[WorkflowTask]
    active_task: Optional[WorkflowTask]
    parallel_branches: List[WorkflowTask] = field(default_factory=list)
    worker_assignments: List[WorkerState] = field(default_factory=list)
    continue_running: bool = True
    merge_plan: str = ""
    stop_reason: str = ""
    memory_summary: str = ""
    artifact_preview: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plannerSource": self.planner_source,
            "currentPhase": self.current_phase,
            "phaseReasoning": self.phase_reasoning,
            "taskQueue": [item.to_dict() for item in self.task_queue],
            "activeTask": self.active_task.to_dict() if self.active_task else None,
            "parallelBranches": [item.to_dict() for item in self.parallel_branches],
            "workerAssignments": [item.to_dict() for item in self.worker_assignments],
            "continueRunning": self.continue_running,
            "mergePlan": self.merge_plan,
            "stopReason": self.stop_reason,
            "memorySummary": self.memory_summary,
            "artifactPreview": self.artifact_preview,
        }


def build_workflow_controller(
    task: str,
    observation: Observation,
    plan: Plan,
    planner_source: str,
    memory: Optional[AgentMemory] = None,
) -> ControllerResult:
    queue = _base_queue(task)
    active_task = next((item for item in queue if item.status == "active"), None) or next((item for item in queue if item.status == "pending"), None)
    branches = _parallel_branches(task, observation)
    workers = [
        WorkerState(
            worker_id=branch.worker_id,
            branch_id=branch.task_id,
            status=branch.status,
            assigned_url=branch.target_url,
            latest_reasoning=branch.reasoning,
            result_summary=branch.result_summary,
        )
        for branch in branches
    ]
    current_phase = active_task.phase if active_task else "verify_and_finalize"
    phase_reasoning = _phase_reasoning(current_phase, task, observation, branches)
    merge_plan = "将各 worker 的结构化 observation、候选摘要和证据片段合并回全局 memory，再由主队列继续收敛。"
    memory_summary = memory.summary() if memory else ""
    artifact_preview = plan.summary
    return ControllerResult(
        planner_source=planner_source,
        current_phase=current_phase,
        phase_reasoning=phase_reasoning,
        task_queue=queue,
        active_task=active_task,
        parallel_branches=branches,
        worker_assignments=workers,
        continue_running=True,
        merge_plan=merge_plan,
        stop_reason="",
        memory_summary=memory_summary,
        artifact_preview=artifact_preview,
    )


def is_parallel_workflow_task(task: str) -> bool:
    return bool(re.search(r"比较|对比|推荐|研究|调研|分析.*项目|分析.*仓库|文档检索|search|compare|research", task, re.I))


def _base_queue(task: str) -> List[WorkflowTask]:
    titles = {
        "observe_ui": "识别界面",
        "understand_user_intent": "理解需求",
        "decompose_task": "拆解任务",
        "plan_execution": "形成规划",
        "execute_browser_actions": "执行浏览器任务",
        "verify_and_finalize": "校验与总结",
    }
    goals = {
        "observe_ui": "识别页面类型、可交互控件和风险区域。",
        "understand_user_intent": "抽取用户目标、约束和完成标准。",
        "decompose_task": "生成阶段任务队列和并行分支候选。",
        "plan_execution": "给当前阶段产出可执行动作计划。",
        "execute_browser_actions": "执行当前阶段动作并收集结果。",
        "verify_and_finalize": "判断是否满足目标，并产出最终 artifact。",
    }
    queue: List[WorkflowTask] = []
    for index, phase in enumerate(PHASES, 1):
        status = "done" if index <= 3 else "pending"
        if index == 4:
            status = "active"
        queue.append(
            WorkflowTask(
                task_id=f"task-{index}",
                phase=phase,
                title=titles[phase],
                goal=goals[phase],
                status=status,
                completion_criteria="该阶段输出已写入 memory 或可见于当前计划。",
                reasoning=f"围绕“{task}”推进 {titles[phase]}。",
            )
        )
    return queue


def _parallel_branches(task: str, observation: Observation) -> List[WorkflowTask]:
    if _is_compare_task(task):
        return _compare_branches(task, observation)
    if _is_research_task(task):
        return _research_branches(task, observation)
    return []


def _compare_branches(task: str, observation: Observation) -> List[WorkflowTask]:
    focus = _clean_compare_focus(task)
    queries = [
        focus or task.strip(),
        f"{focus or task.strip()} 推荐 评测",
        f"{focus or task.strip()} 价格 对比",
    ]
    branches: List[WorkflowTask] = []
    for index, query in enumerate(dict.fromkeys(query.strip() for query in queries if query.strip()), 1):
        branches.append(
            WorkflowTask(
                task_id=f"branch-search-{index}",
                parent_task_id="task-5",
                phase="execute_browser_actions",
                title=f"并行搜索 {index}",
                goal=f"搜索并收集与“{query}”相关的候选。",
                status="pending",
                worker_id=f"worker-{index}",
                execution_mode="parallel",
                target_url=DEFAULT_SEARCH_URL + quote(query),
                merge_key="candidate_pool",
                completion_criteria="返回结构化候选卡片或搜索结果摘要。",
                reasoning=f"为比较任务补充第 {index} 组外部候选证据。",
            )
        )
    return branches


def _research_branches(task: str, observation: Observation) -> List[WorkflowTask]:
    links = [link for link in observation.links[:6] if str(link.get("href") or "").startswith(("http://", "https://"))]
    branches: List[WorkflowTask] = []
    for index, link in enumerate(links[:3], 1):
        branches.append(
            WorkflowTask(
                task_id=f"branch-link-{index}",
                parent_task_id="task-5",
                phase="execute_browser_actions",
                title=f"并行来源分析 {index}",
                goal=f"打开并分析来源：{link.get('text') or link.get('href')}",
                status="pending",
                worker_id=f"worker-{index}",
                execution_mode="parallel",
                target_url=str(link.get("href") or ""),
                merge_key="source_graph",
                completion_criteria="提取来源摘要、关键信息和下一步建议。",
                reasoning="并行读取多个来源，加速资料汇总。",
            )
        )
    if not branches:
        cards = [card for card in observation.cards[:3] if str(card.get("href") or "").startswith(("http://", "https://"))]
        for index, card in enumerate(cards, 1):
            branches.append(
                WorkflowTask(
                    task_id=f"branch-card-{index}",
                    parent_task_id="task-5",
                    phase="execute_browser_actions",
                    title=f"并行候选采样 {index}",
                    goal=f"打开候选页：{card.get('title') or card.get('href')}",
                    status="pending",
                    worker_id=f"worker-{index}",
                    execution_mode="parallel",
                    target_url=str(card.get("href") or ""),
                    merge_key="source_graph",
                    completion_criteria="写回候选摘要和来源 evidence。",
                    reasoning="并行采样多个候选页，补充研究证据。",
                )
            )
    return branches


def _phase_reasoning(current_phase: str, task: str, observation: Observation, branches: List[WorkflowTask]) -> str:
    if current_phase == "plan_execution":
        if branches:
            return f"已识别到 {len(branches)} 个可并行分支，先拆需求再把搜索/采样任务分发给多个 worker。"
        return f"当前任务“{task}”先进入阶段化规划，再决定是否需要派生并行 worker。"
    if current_phase == "execute_browser_actions":
        return "当前进入浏览器执行阶段，按主队列或分支队列逐项消费动作。"
    return f"当前页面标题为“{observation.title}”，系统正在推进阶段：{current_phase}。"


def _is_compare_task(task: str) -> bool:
    return bool(re.search(r"比较|对比|推荐|性价比|compare|rank", task, re.I))


def _is_research_task(task: str) -> bool:
    return bool(re.search(r"研究|调研|分析.*项目|分析.*仓库|文档检索|分析这个 GitHub 仓库|research", task, re.I))


def _clean_compare_focus(command: str) -> str:
    cleaned = re.sub(r"帮我|请|比较|对比|排序|哪个更好|哪个更适合|推荐|这些|方案|产品|工具|search|compare|rank", " ", command, flags=re.I)
    cleaned = re.sub(r"[：:]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()
