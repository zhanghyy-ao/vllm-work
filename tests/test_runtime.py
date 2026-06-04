from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from browser_agent.browser.action import execute_action
from browser_agent.browser.observer import observe
from browser_agent.config import AgentConfig
from browser_agent.evaluation.metrics import summarize_metrics
from browser_agent.harness.runtime import HarnessRuntime
from browser_agent.llm.agent import plan_next_action
from browser_agent.market.compare import compare_market_profiles
from browser_agent.planner.tot import plan_goal
from browser_agent.types import ActionResult, Observation
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
    def test_default_model_config_targets_openai_compatible_multimodal_planner(self) -> None:
        config = AgentConfig()

        self.assertEqual(config.provider, "openai_compatible")
        self.assertEqual(config.model, "gpt-5.5")
        self.assertEqual(config.api_base_url, "https://synai996.space/v1")
        self.assertEqual(config.api_key_env, "BROWSER_AGENT_API_KEY")
        self.assertEqual(config.vision_provider, "openai_compatible")
        self.assertEqual(config.vision_model, "gpt-5.5")
        self.assertEqual(config.vision_api_base_url, "https://synai996.space/v1")
        self.assertEqual(config.vision_api_key_env, "BROWSER_AGENT_API_KEY")
        self.assertEqual(config.model_fallbacks, ["gpt-5.4", "gpt-5.4-mini"])
        self.assertEqual(config.vision_model_fallbacks, ["gpt-5.4", "gpt-5.4-mini"])

    def test_runtime_requires_handoff_for_sensitive_actions(self) -> None:
        runtime = HarnessRuntime(max_steps=8)
        result = runtime.run(GOALS["booking"], "https://example.com")
        self.assertFalse(result["ok"])
        self.assertEqual(result["workflow"]["domain"], "booking")
        self.assertEqual(result["workflow"]["template"], "booking_workflow")
        self.assertEqual(result["llm"]["dynamic_agent_loop"]["used"], False)

    def test_runtime_emits_workflow_metadata_with_auto_approval(self) -> None:
        runtime = HarnessRuntime(max_steps=8, auto_approve_sensitive=True)
        result = runtime.run("\u5e2e\u6211\u9884\u7ea6\u4e0a\u6d77\u5468\u672b\u9152\u5e97", "https://example.com")
        self.assertEqual(result["workflow"]["domain"], "booking")
        self.assertEqual(result["workflow"]["template"], "booking_workflow")
        self.assertIn("evidence_checklist", result["llm"]["plan"])
        self.assertIn("metrics", result)
        self.assertIn("report", result)

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

        self.assertIn('"domain": "monitoring"', completed.stdout)
        self.assertTrue(latest_run.exists())

        payload = json.loads(latest_run.read_text(encoding="utf-8"))
        self.assertEqual(payload["workflow"]["domain"], "monitoring")
        self.assertEqual(payload["workflow"]["template"], "monitoring_workflow")


class DynamicAgentPlannerTests(unittest.TestCase):
    def test_plan_next_action_uses_observation_and_model_decision(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                self.last_user = json.loads(user)
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "当前页面已经有搜索结果，应先抽取候选链接。",
                    "checklist_status": [{"stage": "candidate_pool", "status": "partial", "evidence": "搜索页已打开"}],
                    "next_action": {
                        "action": "collect_links",
                        "instruction": "抽取当前搜索页上的候选商品链接",
                        "inputs": {"source": "shopping", "evidence_stage": "candidate_pool"},
                    },
                }

        workflow = plan_goal(
            "预算1000元以内，推荐一款适合通勤和办公室使用的降噪耳机",
            Observation(url="https://www.bing.com", title="", text=""),
            domain="shopping",
        )
        observation = Observation(
            url="https://www.bing.com/search?q=1000元以内+降噪耳机",
            title="Bing 搜索",
            text="Sony WH-CH720N 降噪耳机 评测",
            elements=[{"text": "Sony WH-CH720N 评测", "href": "https://example.com/sony"}],
        )
        client = FakeClient()
        decision = plan_next_action(workflow, observation, {"evidence": [], "traces": []}, [], client, 1)

        self.assertTrue(decision["ok"])
        self.assertEqual(decision["node"].action, "collect_links")
        self.assertEqual(decision["node"].inputs["evidence_stage"], "candidate_pool")
        self.assertIn("current_page", client.last_user)
        self.assertEqual(client.last_user["current_page"]["candidate_count"], 1)
        self.assertEqual(client.last_user["evidence_checklist"][0]["stage"], "candidate_pool")
        self.assertEqual(client.last_user["evidence_checklist"][0]["status"], "partial")

    def test_plan_next_action_supports_grounded_element_actions(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                self.last_user = json.loads(user)
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "需要在搜索框中输入更具体的查询。",
                    "next_action": {
                        "action": "type_text",
                        "instruction": "在搜索框输入耳机差评查询",
                        "inputs": {"source": "shopping", "element_ref": 0, "text": "WH-CH720N 用户差评", "clear": True},
                    },
                }

        workflow = plan_goal("查找耳机差评", Observation(url="https://www.bing.com", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://www.bing.com",
            title="Bing",
            text="",
            elements=[{"element_id": 0, "role": "searchbox", "name": "搜索", "selector": '[data-agent-idx="0"]'}],
            form_fields=[{"element_id": 0, "role": "searchbox", "name": "搜索"}],
            visible_buttons=[{"element_id": 1, "role": "button", "name": "提交"}],
            accessibility_tree=[{"element_id": 0, "role": "searchbox", "name": "搜索"}],
            visual_summary="页面有一个搜索框和提交按钮",
        )
        client = FakeClient()
        decision = plan_next_action(workflow, observation, {"evidence": [], "traces": []}, [], client, 1)

        self.assertTrue(decision["ok"])
        self.assertEqual(decision["node"].action, "type_text")
        self.assertEqual(decision["node"].inputs["element_ref"], 0)
        self.assertEqual(client.last_user["current_page"]["form_fields"][0]["role"], "searchbox")
        self.assertIn("visual_summary", client.last_user["current_page"])

    def test_plan_next_action_uses_multimodal_chat_when_screenshot_exists(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json_with_image(self, system, user, image_path, temperature=0.1):  # noqa: ANN001
                self.used_image = True
                self.image_path = image_path
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "截图显示需要向下滚动查看更多结果。",
                    "next_action": {
                        "action": "scroll",
                        "instruction": "向下滚动查看更多搜索结果",
                        "inputs": {"source": "shopping", "direction": "down", "pixels": 700},
                    },
                }

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                self.used_text_fallback = True
                return {"ok": False, "error": "should_not_use_text_fallback"}

        workflow = plan_goal("推荐降噪耳机", Observation(url="https://www.bing.com", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://www.bing.com/search?q=耳机",
            title="Bing",
            text="搜索结果",
            screenshot_path="runs/screenshots/fake.png",
        )
        client = FakeClient()
        decision = plan_next_action(workflow, observation, {"evidence": [], "traces": []}, [], client, 1)

        self.assertTrue(decision["ok"])
        self.assertTrue(decision["multimodal_planning_used"])
        self.assertEqual(decision["node"].action, "scroll")
        self.assertEqual(client.image_path, "runs/screenshots/fake.png")

    def test_progress_guard_collects_links_after_search_page(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "搜索结果页看起来还不完整，换一个搜索词。",
                    "next_action": {
                        "action": "search_web",
                        "instruction": "继续搜索耳机推荐",
                        "inputs": {
                            "source": "shopping",
                            "query": "1000元以内 降噪耳机 推荐",
                            "evidence_stage": "candidate_pool",
                        },
                    },
                }

        workflow = plan_goal("推荐1000元以内降噪耳机", Observation(url="", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://www.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA",
            title="Bing 搜索",
            text="搜索结果页",
        )
        memory = {
            "evidence": [],
            "traces": [
                {
                    "node": {"action": "search_web", "inputs": {"query": "1000元以内 降噪耳机"}},
                    "output": {"url": observation.url},
                    "verdict": {"ok": True},
                }
            ],
        }
        decision = plan_next_action(workflow, observation, memory, [], FakeClient(), 2)

        self.assertTrue(decision["ok"])
        self.assertTrue(decision["progress_guard_applied"])
        self.assertEqual(decision["node"].action, "collect_links")
        self.assertEqual(decision["node"].inputs["query"], "1000元以内 降噪耳机 推荐")
        self.assertEqual(decision["node"].inputs["planner_suggested_action"], "search_web")

    def test_progress_guard_deep_reads_after_collected_links(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "候选页可能还没加载，先等待。",
                    "next_action": {
                        "action": "wait",
                        "instruction": "等待页面加载",
                        "inputs": {"source": "github", "evidence_stage": "repo_metadata", "ms": 1000},
                    },
                }

        workflow = plan_goal("对比浏览器 agent 仓库", Observation(url="", title="", text=""), domain="github")
        observation = Observation(
            url="https://github.com/search?q=browser-use&type=repositories",
            title="Repository search results",
            text="browser-use",
            elements=[{"text": "browser-use/browser-use", "href": "https://github.com/browser-use/browser-use"}],
        )
        memory = {
            "evidence": [],
            "traces": [
                {
                    "node": {"action": "collect_links", "inputs": {"source": "github"}},
                    "output": {"fields": {"links": [{"text": "browser-use/browser-use", "href": "https://github.com/browser-use/browser-use"}]}},
                    "verdict": {"ok": True},
                }
            ],
        }
        decision = plan_next_action(workflow, observation, memory, [], FakeClient(), 3)

        self.assertTrue(decision["ok"])
        self.assertTrue(decision["progress_guard_applied"])
        self.assertEqual(decision["node"].action, "deep_read_candidates")
        self.assertEqual(decision["node"].inputs["limit"], 3)
        self.assertEqual(decision["node"].inputs["planner_suggested_action"], "wait")

    def test_dynamic_checklist_marks_completed_and_missing_stages_from_context(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                self.last_user = json.loads(user)
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "根据当前证据缺口，继续补用户评论。",
                    "next_action": {
                        "action": "search_web",
                        "instruction": "搜索用户评论和差评",
                        "inputs": {
                            "source": "shopping",
                            "query": "WH-CH720N Space Q45 用户评论 差评",
                            "evidence_stage": "user_comments",
                        },
                    },
                }

        workflow = plan_goal("推荐1000元以内降噪耳机", Observation(url="", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://www.whathifi.com/reviews/sony-wh-ch720n",
            title="Sony WH-CH720N review",
            text="review compare comfort ANC drawbacks",
            elements=[{"text": "review", "href": "https://www.whathifi.com/reviews/sony-wh-ch720n"}],
        )
        memory = {
            "evidence": [
                {"claim": "candidate link", "support": "Sony WH-CH720N 价格"},
                {"claim": "expert review", "support": "review compare comfort drawbacks"},
            ],
            "traces": [
                {
                    "node": {"action": "collect_links", "inputs": {"evidence_stage": "candidate_pool"}},
                    "verdict": {"ok": True},
                    "output": {"fields": {"links": [{"text": "Sony", "href": "https://example.com"}]}},
                },
                {
                    "node": {"action": "deep_read_candidates", "inputs": {"evidence_stage": "comparative_reviews"}},
                    "verdict": {"ok": True},
                    "output": {"fields": {"evidence_stage": "comparative_reviews"}},
                },
            ],
        }
        step_outputs = [
            {"node_id": "d1", "action": "collect_links", "ok": True, "detail": {"fields": {"evidence_stage": "candidate_pool"}}},
            {"node_id": "d2", "action": "deep_read_candidates", "ok": True, "detail": {"fields": {"evidence_stage": "comparative_reviews"}}},
        ]
        client = FakeClient()
        decision = plan_next_action(workflow, observation, memory, step_outputs, client, 3)

        self.assertTrue(decision["ok"])
        checklist = {item["stage"]: item for item in client.last_user["evidence_checklist"]}
        self.assertEqual(checklist["candidate_pool"]["status"], "satisfied")
        self.assertEqual(checklist["comparative_reviews"]["status"], "satisfied")
        self.assertEqual(checklist["user_comments"]["status"], "missing")

    def test_observation_merges_interactable_snapshot_fields(self) -> None:
        previous = Observation(url="https://example.com", title="old", text="")
        result = ActionResult(
            ok=True,
            action="extract_page",
            url="https://example.com",
            title="new",
            text="body",
            fields={
                "interactable_elements": [{"element_id": 0, "role": "button", "name": "搜索", "selector": "[data-agent-idx='0']"}],
                "form_fields": [{"element_id": 1, "role": "textbox", "name": "关键词"}],
                "visible_buttons": [{"element_id": 0, "role": "button", "name": "搜索"}],
                "accessibility_tree": [{"element_id": 0, "role": "button", "name": "搜索"}],
                "screenshot_path": "runs/screenshots/test.png",
                "visual_summary": "可见搜索按钮",
            },
        )
        obs = result.to_observation(previous)
        self.assertEqual(obs.elements[0]["role"], "button")
        self.assertEqual(obs.form_fields[0]["role"], "textbox")
        self.assertEqual(obs.visible_buttons[0]["name"], "搜索")
        self.assertEqual(obs.visual_summary, "可见搜索按钮")

    def test_task_level_metrics_include_checklist_and_grounding(self) -> None:
        run_result = {
            "goal": "预算1000元以内，推荐降噪耳机",
            "workflow": {
                "domain": "shopping",
                "nodes": [
                    {"id": "d1", "inputs": {"evidence_stage": "candidate_pool"}},
                    {"id": "d2", "inputs": {"evidence_stage": "marketplace_pages"}},
                    {"id": "d3", "inputs": {"evidence_stage": "comparative_reviews"}},
                ],
            },
            "steps": [
                {"node_id": "d1", "ok": True, "detail": {"url": "https://example.com/a", "title": "降噪耳机", "fields": {"evidence_stage": "candidate_pool"}}},
                {"node_id": "d2", "ok": True, "detail": {"url": "https://example.com/b", "title": "1000元以内", "fields": {"evidence_stage": "marketplace_pages"}}},
                {"node_id": "d3", "ok": True, "detail": {"url": "https://example.com/c", "title": "评测", "fields": {"evidence_stage": "comparative_reviews"}}},
            ],
            "memory": {"evidence": [{"source_url": "https://example.com/a", "claim": "candidate", "support": "Sony"}]},
            "report": {
                "summary": "基于证据推荐",
                "recommendations": [{"name": "Sony", "url": "https://example.com/a"}],
                "citations": [{"source_url": "https://example.com/a", "claim": "candidate", "confidence": 0.8}],
            },
        }
        metrics = summarize_metrics(run_result)
        self.assertGreater(metrics["checklist_coverage"], 0.0)
        self.assertEqual(metrics["final_answer_groundedness"], 1.0)
        self.assertEqual(metrics["source_citation_correctness"], 1.0)


class MarketComparisonTests(unittest.TestCase):
    def test_market_comparison_exposes_advantages(self) -> None:
        report = compare_market_profiles("qa_regression")
        self.assertEqual(report["leader"], "Browser Copilot Harness")
        self.assertIn("deterministic_tests", report["our_advantage_capabilities"])
        self.assertEqual(report["best_external"], "OpenAI Operator / ChatGPT agent")


if __name__ == "__main__":
    unittest.main()
