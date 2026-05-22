from __future__ import annotations

import unittest
from unittest.mock import patch

from agent_py import observe_html, plan_task
from agent_py.memory import AgentMemory
from agent_py.runner import BrowserAgentRunner
from agent_py.workflow import BranchResult, build_workflow_controller


HTML = """
<html>
  <head><title>Compare Page</title></head>
  <body>
    <input type="search" aria-label="搜索" placeholder="搜索主题" />
    <button>搜索</button>
    <article data-agent-card="1">
      <h2>耳机 A</h2>
      <p>评分 4.7，价格 ¥499，适合降噪。</p>
      <a href="https://example.com/a">详情</a>
    </article>
    <article data-agent-card="1">
      <h2>耳机 B</h2>
      <p>评分 4.5，价格 ¥399，适合性价比。</p>
      <a href="https://example.com/b">详情</a>
    </article>
  </body>
</html>
"""


class WorkflowControllerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.observation = observe_html(HTML, "https://example.com")

    def test_compare_controller_builds_parallel_branches(self) -> None:
        plan = plan_task("比较性价比最高的耳机", self.observation)
        controller = build_workflow_controller("比较性价比最高的耳机", self.observation, plan, "python-rule")
        self.assertEqual(controller.current_phase, "plan_execution")
        self.assertTrue(controller.parallel_branches)
        self.assertTrue(any(branch.execution_mode == "parallel" for branch in controller.parallel_branches))

    def test_memory_merges_parallel_branch_results(self) -> None:
        memory = AgentMemory(task="比较性价比最高的耳机")
        memory.remember_workflow(
            task_queue=[{"taskId": "task-1"}],
            workers=[{"workerId": "worker-1", "status": "pending"}],
            branches=[{"taskId": "branch-search-1", "workerId": "worker-1"}],
        )
        memory.merge_branch_result(
            {
                "branchId": "branch-search-1",
                "workerId": "worker-1",
                "targetUrl": "https://example.com/a",
                "summary": "来源摘要",
                "data": {
                    "cards": [{"title": "耳机 A", "summary": "评分 4.7，价格 ¥499", "href": "https://example.com/a"}],
                    "headings": ["耳机 A"],
                },
            }
        )
        self.assertTrue(memory.candidate_pool)
        self.assertTrue(memory.merge_log)
        self.assertFalse(memory.open_branches)

    def test_runner_parallel_branch_collection(self) -> None:
        runner = BrowserAgentRunner()
        controller = build_workflow_controller("比较性价比最高的耳机", self.observation, plan_task("比较性价比最高的耳机", self.observation), "python-rule")
        memory = AgentMemory(task="比较性价比最高的耳机")
        fake_result = BranchResult(
            branch_id="branch-search-1",
            worker_id="worker-1",
            status="done",
            target_url="https://example.com/a",
            summary="worker summary",
            data={"cards": [{"title": "耳机 A", "summary": "好用", "href": "https://example.com/a"}]},
        )
        with patch.object(BrowserAgentRunner, "_execute_branch_worker", return_value=fake_result):
            results = runner._run_parallel_branches(controller, memory)
        self.assertTrue(results)
        self.assertEqual(results[0].worker_id, "worker-1")


if __name__ == "__main__":
    unittest.main()
