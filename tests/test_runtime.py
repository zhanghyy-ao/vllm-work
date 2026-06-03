from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from browser_agent.browser.action import execute_action
from browser_agent.browser.observer import observe
from browser_agent.harness.runtime import HarnessRuntime
from browser_agent.market.compare import compare_market_profiles
from browser_agent.planner.tot import plan_goal
from browser_agent.verifier.critic import verify_step


GOALS = {
    "compare": "\u5e2e\u6211\u6bd4\u8f83\u4e09\u6b3e\u8033\u673a\u5e76\u63a8\u8350",
    "form": "\u5e2e\u6211\u586b\u5199\u62a5\u540d\u8868\u5355",
    "research": "\u8c03\u7814\u8fd1\u671f\u6d4f\u89c8\u5668\u667a\u80fd\u4f53\u4ea7\u54c1",
    "booking": "\u5e2e\u6211\u9884\u7ea6\u660e\u665a 7 \u70b9\u7684\u9910\u5385",
    "lead": "\u5e2e\u6211\u641c\u96c6 20 \u4e2a\u6f5c\u5728\u5ba2\u6237\u90ae\u7bb1",
    "monitor": "\u76d1\u63a7\u8fd9\u5bb6\u5e97\u7684\u4ef7\u683c\u53d8\u5316\u5e76\u63d0\u9192\u6211",
    "qa": "\u68c0\u67e5\u767b\u5f55\u9875\u9762\u6709\u6ca1\u6709\u56de\u5f52\u95ee\u9898",
}


class PlannerScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.observation = observe("https://example.com")

    def assertScenario(self, goal: str, expected: str) -> None:
        plan = plan_goal(goal, self.observation)
        self.assertEqual(plan.scenario, expected)
        self.assertGreater(len(plan.actions), 0)

    def test_original_scenarios(self) -> None:
        self.assertScenario(GOALS["compare"], "comparison_recommendation")
        self.assertScenario(GOALS["form"], "form_filling")
        self.assertScenario(GOALS["research"], "research")

    def test_new_scenarios(self) -> None:
        self.assertScenario(GOALS["booking"], "booking_reservation")
        self.assertScenario(GOALS["lead"], "lead_collection")
        self.assertScenario(GOALS["monitor"], "monitoring_alerts")
        self.assertScenario(GOALS["qa"], "qa_regression")


class ExecutionTests(unittest.TestCase):
    def test_new_tools_execute_and_verify(self) -> None:
        observation = observe("https://example.com")
        for tool in ["reserve", "extract_leads", "set_alert", "report_bug"]:
            action = type("A", (), {"tool": tool, "reason": "test", "target": "", "value": ""})()
            output = execute_action(action, observation)
            verdict = verify_step(tool, output, observation)
            self.assertTrue(output["ok"])
            self.assertTrue(verdict["ok"])


class RuntimeTests(unittest.TestCase):
    def test_runtime_requires_handoff_for_sensitive_actions(self) -> None:
        runtime = HarnessRuntime(max_steps=8)
        result = runtime.run(GOALS["booking"], "https://example.com")
        self.assertFalse(result["ok"])
        self.assertEqual(result["scenario"], "booking_reservation")
        self.assertEqual(result["steps"][-1]["reason"], "awaiting_user_approval")
        self.assertEqual(result["approval_requests"][0]["tool"], "reserve")

    def test_runtime_emits_metrics_and_steps_with_auto_approval(self) -> None:
        runtime = HarnessRuntime(max_steps=8, auto_approve_sensitive=True)
        result = runtime.run("\u5e2e\u6211\u9884\u7ea6\u4e0a\u6d77\u5468\u672b\u9152\u5e97", "https://example.com")
        self.assertTrue(result["ok"])
        self.assertEqual(result["scenario"], "booking_reservation")
        self.assertEqual(result["metrics"]["task_success"], 1.0)
        self.assertEqual(len(result["steps"]), 4)
        self.assertIn("market_comparison", result)
        self.assertEqual(result["market_comparison"]["leader"], "Browser Copilot Harness")

    def test_cli_writes_latest_run(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        latest_run = repo_root / "runs" / "latest-run.json"
        if latest_run.exists():
            latest_run.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                "app.py",
                "--goal",
                GOALS["monitor"],
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            check=True,
        )

        self.assertIn('"scenario": "monitoring_alerts"', completed.stdout)
        self.assertTrue(latest_run.exists())

        payload = json.loads(latest_run.read_text(encoding="utf-8"))
        self.assertEqual(payload["scenario"], "monitoring_alerts")
        self.assertTrue(payload["ok"])


class MarketComparisonTests(unittest.TestCase):
    def test_market_comparison_exposes_advantages(self) -> None:
        report = compare_market_profiles("qa_regression")
        self.assertEqual(report["leader"], "Browser Copilot Harness")
        self.assertIn("deterministic_tests", report["our_advantage_capabilities"])
        self.assertEqual(report["best_external"], "OpenAI Operator / ChatGPT agent")


if __name__ == "__main__":
    unittest.main()
