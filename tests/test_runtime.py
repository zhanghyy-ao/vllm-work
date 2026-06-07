from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

import backend_api
from browser_agent.browser.action import execute_action
from browser_agent.browser.observer import observe
from browser_agent.config import AgentConfig
from browser_agent.evaluation.metrics import summarize_metrics
from browser_agent.harness.runtime import HarnessRuntime
from browser_agent.agents.supervisor import plan_next_step
from browser_agent.agents.navigator import (
    _stage_affinity_score,
    build_agent_step_context,
    contextual_evidence_checklist,
    evidence_checklist,
    preferred_stage_for_page,
    requirement_driven_query,
    stage_present_in_evidence,
    stage_visible_on_current_page,
)
from browser_agent.agents.stage_policy import stage_affinity_score as policy_stage_affinity_score
from browser_agent.llm.agent import _workflow_strategy, plan_next_action
from browser_agent.market.compare import compare_market_profiles
from browser_agent.output.report_builder import build_report
from browser_agent.planner.tot import plan_goal
from browser_agent.types import ActionResult, Observation, WorkflowNode
from browser_agent.verifier.critic import verify_node, verify_step
from browser_agent.browser.action import BrowserSession


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
    def test_backend_resume_observation_maps_controls_into_interactable_fields(self) -> None:
        observation = backend_api._observation_from_payload(  # pylint: disable=protected-access
            {
                "url": "https://github.com",
                "title": "GitHub",
                "text": "Search and browse repositories",
                "links": [
                    {"text": "browser-use/browser-use", "url": "https://github.com/browser-use/browser-use"},
                ],
                "controls": [
                    {"index": 0, "tag": "input", "type": "search", "role": "", "label": "Search or jump to", "visible": True, "disabled": False},
                    {"index": 1, "tag": "button", "type": "submit", "role": "", "label": "Search", "visible": True, "disabled": False},
                ],
            },
            "https://example.com",
        )

        self.assertEqual(observation.url, "https://github.com")
        self.assertEqual(len(observation.form_fields), 1)
        self.assertEqual(observation.form_fields[0]["role"], "searchbox")
        self.assertEqual(observation.form_fields[0]["element_id"], 0)
        self.assertEqual(len(observation.visible_buttons), 1)
        self.assertEqual(observation.visible_buttons[0]["role"], "button")
        self.assertTrue(any(item.get("href") == "https://github.com/browser-use/browser-use" for item in observation.elements))
        self.assertTrue(any(item.get("element_id") == 0 for item in observation.accessibility_tree))

    def test_collect_links_uses_current_links_and_github_api_fallback_without_seed_library(self) -> None:
        class FakePage:
            url = "https://github.com/search?q=browser+agent&type=repositories"

            def title(self):  # noqa: ANN001
                return "Repository search results"

        session = BrowserSession(headless=True)
        session.page = FakePage()
        session._search_result_links = lambda: []  # noqa: SLF001
        session._github_api_links = lambda query: [  # noqa: SLF001
            {"text": "browser-use/browser-use (123 stars)", "href": "https://github.com/browser-use/browser-use"},
        ]
        session._body_text = lambda: "browser automation agent repositories"  # noqa: SLF001
        session._page_snapshot_fields = lambda node_id: {"interactable_elements": [], "accessibility_tree": [], "form_fields": [], "visible_buttons": [], "visual_summary": "", "screenshot_path": ""}  # noqa: ARG005,SLF001

        node = WorkflowNode(
            id="d1",
            type="agent_dynamic",
            instruction="collect repo candidates",
            action="collect_links",
            inputs={"source": "github", "query": "browser automation agent", "requirement_slot": "repo_candidates"},
        )
        observation = Observation(url=FakePage.url, title="GitHub", text="search page")

        result = session._collect_links(node, observation)  # pylint: disable=protected-access

        self.assertTrue(result.ok)
        self.assertEqual(result.fields["links"][0]["href"], "https://github.com/browser-use/browser-use")
        self.assertEqual(result.fields["repo_candidate_signals"]["slot"], "repo_candidates")

    def test_collect_links_uses_observation_links_when_page_link_extraction_is_empty(self) -> None:
        class FakePage:
            url = "https://www.bing.com/search?q=headphones"

            def title(self):  # noqa: ANN001
                return "Search results"

        session = BrowserSession(headless=True)
        session.page = FakePage()
        session._search_result_links = lambda: []  # noqa: SLF001
        session._body_text = lambda: "search results for ANC headphones"  # noqa: SLF001
        session._page_snapshot_fields = lambda node_id: {"interactable_elements": [], "accessibility_tree": [], "form_fields": [], "visible_buttons": [], "visual_summary": "", "screenshot_path": ""}  # noqa: ARG005,SLF001

        node = WorkflowNode(
            id="d1",
            type="agent_dynamic",
            instruction="collect shopping candidates",
            action="collect_links",
            inputs={"source": "shopping", "query": "1000元以内降噪耳机 通勤 评测 对比", "requirement_slot": "candidate_pool"},
        )
        observation = Observation(
            url=FakePage.url,
            title="Bing",
            text="search page",
            elements=[
                {"text": "Sony WH-CH720N review", "href": "https://www.whathifi.com/reviews/sony-wh-ch720n"},
                {"text": "Soundcore Space Q45 review", "href": "https://www.rtings.com/headphones/reviews/anker/soundcore-space-q45-wireless"},
            ],
        )

        result = session._collect_links(node, observation)  # pylint: disable=protected-access

        self.assertTrue(result.ok)
        self.assertEqual(len(result.fields["links"]), 2)
        self.assertEqual(result.fields["links"][0]["href"], "https://www.whathifi.com/reviews/sony-wh-ch720n")
        self.assertEqual(result.fields["candidate_pool_signals"]["slot"], "candidate_pool")

    def test_search_web_executes_in_page_searchbox_before_external_search_url(self) -> None:
        session = BrowserSession(headless=True)
        session._find_searchbox_ref = lambda observation: 7  # noqa: SLF001
        session._type_text = lambda node, observation: ActionResult(  # noqa: SLF001
            ok=True,
            action="type_text",
            url=observation.url,
            title=observation.title,
            text="typed into searchbox",
            fields={
                "element_ref": node.inputs.get("element_ref"),
                "text": node.inputs.get("text"),
                "submit_after_type": {"ok": True, "method": "press_enter"},
            },
        )
        session._goto = lambda url, node, claim="Opened page": ActionResult(ok=False, action="goto", url=url, error="should_not_use_external_search")  # noqa: ARG005,SLF001

        node = WorkflowNode(
            id="d2",
            type="agent_dynamic",
            instruction="search current site",
            action="search_web",
            inputs={"source": "github", "query": "browser automation agent"},
        )
        observation = Observation(
            url="https://github.com",
            title="GitHub",
            text="Search or jump to repositories",
            elements=[{"element_id": 7, "role": "searchbox", "name": "Search or jump to"}],
            form_fields=[{"element_id": 7, "role": "searchbox", "name": "Search or jump to"}],
        )

        result = session._search_web(node, observation)  # pylint: disable=protected-access

        self.assertTrue(result.ok)
        self.assertEqual(result.fields["element_ref"], 7)
        self.assertEqual(result.fields["text"], "browser automation agent")
        self.assertEqual(result.fields["search_execution_mode"], "in_page_searchbox")

    def test_type_text_fails_when_submit_after_type_does_not_advance_page(self) -> None:
        class FakeLocator:
            def fill(self, value, timeout=5000):  # noqa: ANN001,ARG002
                return None

        class FakePage:
            url = "https://github.com"

            def title(self):  # noqa: ANN001
                return "GitHub"

        session = BrowserSession(headless=True)
        session.page = FakePage()
        session._locator_for_ref = lambda node, observation: FakeLocator()  # noqa: ARG005,SLF001
        session._submit_after_typing = lambda locator, observation: {"ok": False, "methods_tried": ["press_enter"]}  # noqa: ARG005,SLF001

        node = WorkflowNode(
            id="d3",
            type="agent_dynamic",
            instruction="type and submit",
            action="type_text",
            inputs={"element_ref": 7, "text": "browser automation agent", "submit_after_type": True},
        )
        observation = Observation(url="https://github.com", title="GitHub", text="Search")

        result = session._type_text(node, observation)  # pylint: disable=protected-access

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "submit_after_type_failed")
        self.assertEqual(result.fields["submit_after_type"]["methods_tried"], ["press_enter"])

    def test_locator_for_element_ref_supports_playwright_first_property(self) -> None:
        class FakeLocatorResult:
            def __init__(self) -> None:
                self.first = "first-locator"

        class FakePage:
            def locator(self, selector):  # noqa: ANN001
                self.last_selector = selector
                return FakeLocatorResult()

        session = BrowserSession(headless=True)
        session.page = FakePage()
        observation = Observation(
            url="https://example.com",
            title="Example",
            text="",
            elements=[{"element_id": 7, "selector": '[data-agent-idx="7"]'}],
        )

        locator = session._locator_for_element_ref(7, observation)  # pylint: disable=protected-access

        self.assertEqual(locator, "first-locator")
        self.assertEqual(session.page.last_selector, '[data-agent-idx="7"]')

    def test_default_model_config_targets_openai_compatible_multimodal_planner(self) -> None:
        config = AgentConfig()

        self.assertEqual(config.provider, "openai_compatible")
        self.assertEqual(config.model, "gpt-5.4")
        self.assertEqual(config.api_base_url, "https://synai996.space/v1")
        self.assertEqual(config.api_key_env, "BROWSER_AGENT_API_KEY")
        self.assertEqual(config.vision_provider, "openai_compatible")
        self.assertEqual(config.vision_model, "gpt-5.4")
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
        self.assertIn("failure_analysis", result)

    def test_general_domain_stays_in_workflow_runtime(self) -> None:
        runtime = HarnessRuntime(max_steps=1)
        self.assertFalse(runtime._should_use_scenario_harness("调研浏览器智能体产品", "general"))

    def test_explicit_general_run_does_not_fall_back_to_scenario_harness(self) -> None:
        runtime = HarnessRuntime(max_steps=1)

        def fail_scenario(_goal, _url):  # noqa: ANN001
            raise AssertionError("general domain should not use scenario harness")

        def fake_workflow(goal, start_url, domain="auto"):  # noqa: ANN001
            return {"ok": True, "goal": goal, "start_url": start_url, "workflow": {"domain": domain}}

        runtime._run_scenario = fail_scenario
        runtime._run_workflow = fake_workflow
        result = runtime.run("调研浏览器智能体产品", "https://example.com", domain="general")
        self.assertTrue(result["ok"])
        self.assertEqual(result["workflow"]["domain"], "general")

    def test_workflow_bootstraps_start_page_before_planning_loop(self) -> None:
        runtime = HarnessRuntime(max_steps=1)
        call_log = []

        class FakeSession:
            def __enter__(self_inner):  # noqa: ANN001
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb):  # noqa: ANN001
                return False

            def observe_current_page(self_inner, previous=None, node_id="observe", seed_fields=None):  # noqa: ANN001
                return Observation(
                    url=previous.url if previous else "https://example.com",
                    title="Example",
                    text="Loaded page",
                    extracted_fields=seed_fields or {},
                )

        def fake_dispatch_node(session, node, observation):  # noqa: ANN001
            call_log.append((node.action, dict(node.inputs)))
            return ActionResult(ok=True, action=node.action, url=node.inputs.get("url", observation.url), title="Example", text="Loaded page")

        def fake_verify_node(node, result, observation):  # noqa: ANN001
            return type("Verdict", (), {"ok": True, "score": 1.0, "to_dict": lambda self: {"ok": True, "score": 1.0}})()

        with mock.patch.object(type(runtime.llm_client), "enabled", new_callable=mock.PropertyMock, return_value=False), \
             mock.patch("browser_agent.harness.runtime.BrowserSession", return_value=FakeSession()), \
             mock.patch("browser_agent.harness.runtime.dispatch_node", side_effect=fake_dispatch_node), \
             mock.patch("browser_agent.harness.runtime.verify_node", side_effect=fake_verify_node):
            result = runtime.run("调研浏览器智能体产品", "https://example.com", domain="general")

        self.assertTrue(result["events"])
        self.assertEqual(call_log[0][0], "goto")
        self.assertEqual(call_log[0][1]["url"], "https://example.com")

    def test_workflow_resume_from_current_observation_skips_bootstrap_goto(self) -> None:
        runtime = HarnessRuntime(max_steps=1)
        call_log = []
        synced_urls = []

        class FakeSession:
            def __enter__(self_inner):  # noqa: ANN001
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb):  # noqa: ANN001
                return False

            def sync_to_observation(self_inner, observation):  # noqa: ANN001
                synced_urls.append(observation.url)

            def observe_current_page(self_inner, previous=None, node_id="observe", seed_fields=None):  # noqa: ANN001
                return previous or Observation(
                    url="https://zhuanlan.zhihu.com/p/1",
                    title="知乎",
                    text="current page",
                    extracted_fields=seed_fields or {},
                )

        def fake_dispatch_node(session, node, observation):  # noqa: ANN001
            call_log.append((node.action, dict(node.inputs)))
            return ActionResult(ok=True, action=node.action, url=node.inputs.get("url", observation.url), title="Example", text="Loaded page")

        def fake_plan_next_step(**kwargs):  # noqa: ANN001
            node = WorkflowNode(
                id="d1",
                type="agent_dynamic",
                instruction="safe fallback",
                action="extract_page",
                inputs={"source": "general"},
            )
            return {"ok": True, "node": node, "agent": "supervisor", "navigator_agent": "navigator", "status": "continue", "supervisor_state": {}}

        def fake_verify_node(node, result, observation):  # noqa: ANN001
            return type("Verdict", (), {"ok": True, "score": 1.0, "to_dict": lambda self: {"ok": True, "score": 1.0}})()

        initial_observation = Observation(url="https://zhuanlan.zhihu.com/p/1", title="知乎", text="current page")

        with mock.patch("browser_agent.harness.runtime.BrowserSession", return_value=FakeSession()), \
             mock.patch("browser_agent.harness.runtime.dispatch_node", side_effect=fake_dispatch_node), \
             mock.patch("browser_agent.harness.runtime.plan_next_step", side_effect=fake_plan_next_step), \
             mock.patch("browser_agent.harness.runtime.verify_node", side_effect=fake_verify_node):
            result = runtime.run("调研浏览器智能体产品", "https://example.com", domain="general", initial_observation=initial_observation)

        self.assertTrue(result["events"])
        self.assertFalse(any(action == "goto" for action, _inputs in call_log))
        self.assertEqual(result["events"][0]["phase"], "bootstrap_resume")
        self.assertEqual(synced_urls, ["https://zhuanlan.zhihu.com/p/1"])

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
    def test_supervisor_delegates_to_navigator(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "当前页已有结果，先抽取候选。",
                    "checklist_status": [{"stage": "candidate_pool", "status": "partial", "evidence": "results page"}],
                    "next_action": {
                        "action": "collect_links",
                        "instruction": "抽取当前页候选链接",
                        "inputs": {"source": "shopping", "evidence_stage": "candidate_pool"},
                    },
                }

        workflow = plan_goal("推荐降噪耳机", Observation(url="https://www.bing.com", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://www.bing.com/search?q=耳机",
            title="Bing 搜索",
            text="搜索结果",
            elements=[{"text": "candidate", "href": "https://example.com"}],
        )
        decision = plan_next_step(workflow, observation, {"evidence": [], "traces": []}, [], FakeClient(), 1)

        self.assertTrue(decision["ok"])
        self.assertEqual(decision["agent"], "supervisor")
        self.assertEqual(decision["navigator_agent"], "navigator")
        self.assertEqual(decision["node"].action, "collect_links")
        self.assertIn("checklist", decision["supervisor_state"])

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

    def test_react_guard_prefers_type_text_over_search_web_when_searchbox_visible(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "先搜索一下更稳妥。",
                    "next_action": {
                        "action": "search_web",
                        "instruction": "搜索浏览器自动化智能体",
                        "inputs": {"source": "general", "query": "browser automation agent"},
                    },
                }

        workflow = plan_goal("调研浏览器自动化智能体", Observation(url="https://github.com", title="", text=""), domain="general")
        observation = Observation(
            url="https://github.com",
            title="GitHub",
            text="Build and ship software on a single, collaborative platform",
            elements=[{"element_id": 0, "role": "searchbox", "name": "Search or jump to", "selector": '[data-agent-idx=\"0\"]'}],
            form_fields=[{"element_id": 0, "role": "searchbox", "name": "Search or jump to"}],
            accessibility_tree=[{"element_id": 0, "role": "searchbox", "name": "Search or jump to"}],
        )
        decision = plan_next_step(workflow, observation, {"evidence": [], "traces": []}, [], FakeClient(), 1)

        self.assertTrue(decision["ok"])
        self.assertTrue(decision.get("react_guard_applied"))
        self.assertEqual(decision["node"].action, "type_text")
        self.assertEqual(decision["node"].inputs["element_ref"], 0)
        self.assertEqual(decision["node"].inputs["text"], "browser automation agent")
        self.assertTrue(decision["node"].inputs["submit_after_type"])
        self.assertEqual(decision["node"].inputs["requirement_slot"], "orientation")

    def test_react_guard_uses_requirement_driven_query_for_review_slot(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "先搜一下。",
                    "next_action": {
                        "action": "search_web",
                        "instruction": "搜索评测",
                        "inputs": {"source": "shopping", "evidence_stage": "comparative_reviews"},
                    },
                }

        workflow = plan_goal("推荐1000元以内降噪耳机", Observation(url="https://www.bing.com", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://www.bing.com",
            title="Bing",
            text="",
            elements=[{"element_id": 0, "role": "searchbox", "name": "搜索", "selector": '[data-agent-idx="0"]'}],
            form_fields=[{"element_id": 0, "role": "searchbox", "name": "搜索"}],
            accessibility_tree=[{"element_id": 0, "role": "searchbox", "name": "搜索"}],
        )
        decision = plan_next_step(workflow, observation, {"evidence": [], "traces": []}, [], FakeClient(), 1)

        self.assertTrue(decision["ok"])
        self.assertEqual(decision["node"].action, "type_text")
        self.assertEqual(decision["node"].inputs["text"], "1000元以内降噪耳机 评测 对比")
        self.assertEqual(decision["node"].inputs["requirement_slot"], "comparative_reviews")

    def test_react_guard_does_not_use_irrelevant_site_searchbox_for_shopping_task(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "先搜一下。",
                    "next_action": {
                        "action": "search_web",
                        "instruction": "搜索评测",
                        "inputs": {"source": "shopping", "evidence_stage": "comparative_reviews"},
                    },
                }

        workflow = plan_goal("推荐1000元以内降噪耳机", Observation(url="https://gitcode.csdn.net", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://gitcode.csdn.net/6a0e707c10ee7a33f274126c.html",
            title="AtomGit开源社区",
            text="AtomGit开源社区 代码托管 仓库 镜像",
            elements=[{"element_id": 15, "role": "searchbox", "name": "搜索", "selector": '[data-agent-idx="15"]'}],
            form_fields=[{"element_id": 15, "role": "searchbox", "name": "搜索"}],
            accessibility_tree=[{"element_id": 15, "role": "searchbox", "name": "搜索"}],
        )
        decision = plan_next_step(workflow, observation, {"evidence": [], "traces": []}, [], FakeClient(), 1)

        self.assertTrue(decision["ok"])
        self.assertNotEqual(decision["node"].action, "type_text")

    def test_react_guard_does_not_open_candidates_from_low_quality_mirror_page(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "继续等一下。",
                    "next_action": {
                        "action": "wait",
                        "instruction": "等待",
                        "inputs": {"source": "general", "evidence_stage": "comparative_reviews"},
                    },
                }

        workflow = plan_goal("推荐1000元以内降噪耳机", Observation(url="https://gitcode.csdn.net", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://gitcode.csdn.net/6a0e707c10ee7a33f274126c.html",
            title="AtomGit开源社区",
            text="AtomGit开源社区 代码托管 仓库 镜像 2026年耳机降噪推荐",
            elements=[{"text": "镜像文章", "href": "https://gitcode.csdn.net/6a0e707c10ee7a33f274126c.html"}],
        )
        memory = {
            "evidence": [],
            "traces": [
                {
                    "node": {"action": "collect_links", "inputs": {"source": "shopping"}},
                    "output": {"fields": {"links": [{"text": "镜像文章", "href": "https://gitcode.csdn.net/6a0e707c10ee7a33f274126c.html"}]}},
                    "verdict": {"ok": True},
                }
            ],
        }
        decision = plan_next_step(workflow, observation, memory, [], FakeClient(), 2)

        self.assertTrue(decision["ok"])
        self.assertNotEqual(decision["node"].action, "open_candidate")
        self.assertNotEqual(decision["node"].action, "deep_read_candidates")

    def test_guard_query_adds_shopping_noise_filters(self) -> None:
        from browser_agent.agents.navigator import _guard_query

        guarded = _guard_query("shopping", "推荐1000元以内降噪耳机", "1000元以内降噪耳机")

        self.assertIn("评测 对比 商品 价格", guarded)
        self.assertIn("-股票 -指数 -中证1000 -基金 -证券", guarded)

    def test_dynamic_type_text_defaults_to_submit_after_type(self) -> None:
        from browser_agent.agents.navigator import _normalize_dynamic_decision

        workflow = plan_goal("推荐1000元以内降噪耳机", Observation(url="https://www.bing.com", title="", text=""), domain="shopping")
        decision = _normalize_dynamic_decision(
            {
                "status": "continue",
                "next_action": {
                    "action": "type_text",
                    "instruction": "输入搜索词",
                    "inputs": {
                        "source": "shopping",
                        "element_ref": 4,
                        "text": "降噪耳机 通勤 办公 商品页",
                    },
                },
            },
            workflow,
            1,
        )

        self.assertTrue(decision["ok"])
        self.assertTrue(decision["node"].inputs["submit_after_type"])

    def test_react_guard_prefers_candidate_open_over_new_search(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "继续搜索可能有更多结果。",
                    "next_action": {
                        "action": "search_web",
                        "instruction": "继续搜索仓库",
                        "inputs": {"source": "github", "query": "browser automation agent"},
                    },
                }

        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")
        observation = Observation(
            url="https://github.com/search?q=browser+automation+agent&type=repositories",
            title="Repository search results",
            text="browser-use stagehand",
            elements=[{"text": "browser-use/browser-use", "href": "https://github.com/browser-use/browser-use"}],
        )
        decision = plan_next_step(workflow, observation, {"evidence": [], "traces": []}, [], FakeClient(), 2)

        self.assertTrue(decision["ok"])
        self.assertTrue(decision.get("react_guard_applied"))
        self.assertEqual(decision["node"].action, "open_candidate")
        self.assertEqual(decision["node"].inputs["rank"], 0)

    def test_open_candidate_prefers_higher_quality_shopping_source(self) -> None:
        session = BrowserSession(headless=True)
        captured = {}

        def fake_goto(url, node, claim="Opened page"):  # noqa: ANN001
            captured["url"] = url
            return ActionResult(ok=True, action=node.action, url=url, title="opened", text=claim)

        session._goto = fake_goto  # noqa: SLF001
        observation = Observation(
            url="https://www.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA",
            title="Bing",
            text="search results",
            elements=[
                {"text": "2026年耳机降噪推荐：7款主流机型实测", "href": "https://gitcode.csdn.net/6a0e707c10ee7a33f274126c.html"},
                {"text": "Sony WH-CH720N review", "href": "https://www.whathifi.com/reviews/sony-wh-ch720n"},
            ],
        )
        node = WorkflowNode(
            id="d1",
            type="agent_dynamic",
            instruction="open best candidate",
            action="open_candidate",
            inputs={"source": "shopping", "rank": 0},
        )

        result = session._open_candidate(node, observation)  # pylint: disable=protected-access

        self.assertTrue(result.ok)
        self.assertEqual(captured["url"], "https://www.whathifi.com/reviews/sony-wh-ch720n")

    def test_open_candidate_prefers_review_source_for_comparative_reviews_even_with_general_source(self) -> None:
        session = BrowserSession(headless=True)
        captured = {}

        def fake_goto(url, node, claim="Opened page"):  # noqa: ANN001
            captured["url"] = url
            return ActionResult(ok=True, action=node.action, url=url, title="opened", text=claim)

        session._goto = fake_goto  # noqa: SLF001
        observation = Observation(
            url="https://www.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA",
            title="Bing",
            text="search results",
            elements=[
                {"text": "2026年耳机降噪推荐：7款主流机型实测", "href": "https://gitcode.csdn.net/6a0e707c10ee7a33f274126c.html"},
                {"text": "Sony WH-CH720N review", "href": "https://www.whathifi.com/reviews/sony-wh-ch720n"},
                {"text": "商品页", "href": "https://www.jd.com/product/123.html"},
            ],
        )
        node = WorkflowNode(
            id="d1",
            type="agent_dynamic",
            instruction="open best comparative review candidate",
            action="open_candidate",
            inputs={"source": "general", "rank": 0, "requirement_slot": "comparative_reviews"},
        )

        result = session._open_candidate(node, observation)  # pylint: disable=protected-access

        self.assertTrue(result.ok)
        self.assertEqual(captured["url"], "https://www.whathifi.com/reviews/sony-wh-ch720n")

    def test_deep_read_candidates_uses_prioritized_shopping_sources(self) -> None:
        session = BrowserSession(headless=True)
        read_order = []

        def fake_read_candidate_page(href, candidate, rank, source):  # noqa: ANN001
            read_order.append(href)
            return {"ok": True, "rank": rank, "name": candidate.get("text"), "url": href, "title": candidate.get("text"), "description": "", "price_signal": "", "source": source, "text": candidate.get("text")}

        session._read_candidate_page = fake_read_candidate_page  # noqa: SLF001
        session._page_snapshot_fields = lambda node_id, existing_screenshot="": {"interactable_elements": [], "accessibility_tree": [], "form_fields": [], "visible_buttons": [], "visual_summary": "", "screenshot_path": existing_screenshot}  # noqa: ARG005,SLF001
        observation = Observation(
            url="https://www.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA",
            title="Bing",
            text="search results",
            elements=[
                {"text": "2026年耳机降噪推荐：7款主流机型实测", "href": "https://gitcode.csdn.net/6a0e707c10ee7a33f274126c.html"},
                {"text": "Sony WH-CH720N review", "href": "https://www.whathifi.com/reviews/sony-wh-ch720n"},
                {"text": "Soundcore Space Q45 review", "href": "https://www.rtings.com/headphones/reviews/anker/soundcore-space-q45-wireless"},
            ],
        )
        node = WorkflowNode(
            id="d2",
            type="agent_dynamic",
            instruction="deep read best candidates",
            action="deep_read_candidates",
            inputs={"source": "shopping", "limit": 2, "requirement_slot": "comparative_reviews"},
        )

        result = session._deep_read_candidates(node, observation)  # pylint: disable=protected-access

        self.assertTrue(result.ok)
        self.assertEqual(read_order[:2], [
            "https://www.rtings.com/headphones/reviews/anker/soundcore-space-q45-wireless",
            "https://www.whathifi.com/reviews/sony-wh-ch720n",
        ])

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

    def test_progress_guard_overrides_scroll_with_open_candidate_on_results_page(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "先滚动查看更多结果。",
                    "next_action": {
                        "action": "scroll",
                        "instruction": "向下滚动查看更多搜索结果",
                        "inputs": {"source": "shopping", "direction": "down", "pixels": 700},
                    },
                }

        workflow = plan_goal("推荐降噪耳机", Observation(url="https://www.bing.com", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://www.bing.com/search?q=耳机",
            title="Bing 搜索",
            text="搜索结果 Sony WH-CH720N review Soundcore Space Q45 review",
            elements=[
                {"text": "Sony WH-CH720N review", "href": "https://www.whathifi.com/reviews/sony-wh-ch720n"},
                {"text": "Soundcore Space Q45 review", "href": "https://www.rtings.com/headphones/reviews/anker/soundcore-space-q45-wireless"},
            ],
        )
        memory_dump = {"evidence": [], "traces": []}
        decision = plan_next_action(workflow, observation, memory_dump, [], FakeClient(), 1)

        self.assertTrue(decision["ok"])
        self.assertEqual(decision["node"].action, "open_candidate")
        self.assertTrue(decision.get("progress_guard_applied"))

    def test_progress_guard_overrides_extract_page_with_collect_links_on_results_page(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "先提取当前页面文本。",
                    "next_action": {
                        "action": "extract_page",
                        "instruction": "提取当前搜索结果页文本",
                        "inputs": {"source": "shopping"},
                    },
                }

        workflow = plan_goal("推荐降噪耳机", Observation(url="https://www.bing.com", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://www.bing.com/search?q=耳机",
            title="Bing 搜索",
            text="搜索结果 Sony WH-CH720N review Soundcore Space Q45 review",
            elements=[
                {"text": "Sony WH-CH720N review", "href": "https://www.whathifi.com/reviews/sony-wh-ch720n"},
                {"text": "Soundcore Space Q45 review", "href": "https://www.rtings.com/headphones/reviews/anker/soundcore-space-q45-wireless"},
            ],
        )
        memory_dump = {"evidence": [], "traces": []}
        decision = plan_next_action(workflow, observation, memory_dump, [], FakeClient(), 1)

        self.assertTrue(decision["ok"])
        self.assertEqual(decision["node"].action, "collect_links")
        self.assertTrue(decision.get("progress_guard_applied"))

    def test_repeat_breaker_promotes_repeated_search_to_deep_read(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "继续搜索更多结果。",
                    "next_action": {
                        "action": "search_web",
                        "instruction": "继续搜索耳机评测",
                        "inputs": {"source": "shopping", "query": "1000元以内降噪耳机 评测 对比"},
                    },
                }

        workflow = plan_goal("推荐1000元以内降噪耳机", Observation(url="https://www.bing.com", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://www.bing.com/search?q=1000%E5%85%83%E4%BB%A5%E5%86%85+%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA",
            title="Bing 搜索",
            text="搜索结果 Sony WH-CH720N review Soundcore Space Q45 review",
            elements=[
                {"text": "Sony WH-CH720N review", "href": "https://www.whathifi.com/reviews/sony-wh-ch720n"},
                {"text": "Soundcore Space Q45 review", "href": "https://www.rtings.com/headphones/reviews/anker/soundcore-space-q45-wireless"},
            ],
        )
        memory_dump = {
            "evidence": [],
            "traces": [
                {
                    "node": {"action": "search_web", "inputs": {"query": "1000元以内降噪耳机 评测 对比"}},
                    "output": {"fields": {}},
                    "verdict": {"ok": True},
                },
                {
                    "node": {"action": "collect_links", "inputs": {"source": "shopping"}},
                    "output": {"fields": {"links": observation.elements}},
                    "verdict": {"ok": True},
                },
            ],
        }
        decision = plan_next_action(workflow, observation, memory_dump, [], FakeClient(), 3)

        self.assertTrue(decision["ok"])
        self.assertTrue(decision.get("repeat_breaker_applied"))
        self.assertEqual(decision["node"].action, "deep_read_candidates")

    def test_repeat_breaker_promotes_repeated_type_text_to_summary_after_deep_read(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "继续搜索更多用户评论。",
                    "next_action": {
                        "action": "type_text",
                        "instruction": "继续搜评论",
                        "inputs": {"source": "shopping", "element_ref": 0, "text": "降噪耳机 用户评论 差评"},
                    },
                }

        workflow = plan_goal("推荐1000元以内降噪耳机", Observation(url="https://www.bing.com", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://www.whathifi.com/reviews/sony-wh-ch720n",
            title="Sony WH-CH720N review",
            text="review verdict ANC comfort battery commute office",
            elements=[],
        )
        memory_dump = {
            "evidence": [],
            "traces": [
                {
                    "node": {"action": "type_text", "inputs": {"text": "降噪耳机 用户评论 差评"}},
                    "output": {"fields": {}},
                    "verdict": {"ok": True},
                },
                {
                    "node": {"action": "deep_read_candidates", "inputs": {"source": "shopping"}},
                    "output": {"fields": {"deep_reads": [{"url": "https://www.whathifi.com/reviews/sony-wh-ch720n", "text": "ANC comfort battery"}]}},
                    "verdict": {"ok": True},
                },
            ],
        }
        decision = plan_next_action(workflow, observation, memory_dump, [], FakeClient(), 3)

        self.assertTrue(decision["ok"])
        self.assertTrue(decision.get("repeat_breaker_applied"))
        self.assertEqual(decision["node"].action, "summarize_text")

    def test_plan_next_action_exposes_requirement_slot_and_page_capabilities_to_llm(self) -> None:
        class FakeClient:
            enabled = True

            def chat_json(self, system, user, temperature=0.1):  # noqa: ANN001
                self.last_user = json.loads(user)
                return {
                    "ok": True,
                    "status": "continue",
                    "rationale": "已有结果，先收集候选。",
                    "next_action": {
                        "action": "collect_links",
                        "instruction": "抽取当前结果页候选",
                        "inputs": {"source": "github", "requirement_slot": "repo_candidates"},
                    },
                }

        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")
        observation = Observation(
            url="https://github.com/search?q=browser+automation+agent&type=repositories",
            title="Repository search results",
            text="browser-use stagehand",
            elements=[{"text": "browser-use/browser-use", "href": "https://github.com/browser-use/browser-use"}],
        )
        client = FakeClient()
        decision = plan_next_action(workflow, observation, {"evidence": [], "traces": []}, [], client, 1)

        self.assertTrue(decision["ok"])
        self.assertEqual(client.last_user["priority_requirement_slot"], "repo_candidates")
        self.assertTrue(client.last_user["current_page_capabilities"]["looks_like_results_page"])
        self.assertTrue(client.last_user["current_page_capabilities"]["has_candidate_links"])

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
        self.assertEqual(checklist["candidate_pool"]["requirement_slot"], "candidate_pool")

    def test_first_missing_stage_prefers_partial_slot_from_current_page(self) -> None:
        from browser_agent.agents.navigator import first_missing_stage

        workflow = plan_goal("推荐1000元以内降噪耳机", Observation(url="", title="", text=""), domain="shopping")
        observation = Observation(
            url="https://www.whathifi.com/reviews/sony-wh-ch720n",
            title="Sony WH-CH720N review",
            text="review compare comfort ANC drawbacks",
            elements=[{"text": "review", "href": "https://www.whathifi.com/reviews/sony-wh-ch720n"}],
        )
        stage = first_missing_stage(workflow, observation, {"evidence": [], "traces": []}, [])
        self.assertEqual(stage, "comparative_reviews")

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

    def test_metrics_cover_requirement_slots(self) -> None:
        metrics = summarize_metrics(
            {
                "goal": "预算1000元以内，推荐一款适合通勤和办公室使用的降噪耳机",
                "workflow": {
                    "domain": "shopping",
                    "nodes": [
                        {"id": "d1", "inputs": {"requirement_slot": "candidate_pool"}},
                        {"id": "d2", "inputs": {"requirement_slot": "marketplace_pages"}},
                        {"id": "d3", "inputs": {"requirement_slot": "comparative_reviews"}},
                    ],
                },
                "steps": [
                    {"node_id": "d1", "ok": True, "detail": {"url": "https://example.com/a", "title": "降噪耳机", "fields": {"requirement_slot": "candidate_pool"}}},
                    {"node_id": "d2", "ok": True, "detail": {"url": "https://example.com/b", "title": "1000元以内", "fields": {"requirement_slot": "marketplace_pages"}}},
                    {"node_id": "d3", "ok": True, "detail": {"url": "https://example.com/c", "title": "评测", "fields": {"requirement_slot": "comparative_reviews"}}},
                ],
                "report": {"summary": "完成调研", "citations": [{"source_url": "https://example.com/a"}]},
                "memory": {"evidence": [{"claim": "x", "support": "y"}]},
            }
        )
        self.assertGreater(metrics["checklist_coverage"], 0.5)

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

    def test_failure_metrics_are_classified_by_type(self) -> None:
        run_result = {
            "goal": "调研浏览器自动化智能体",
            "workflow": {"domain": "github", "nodes": []},
            "steps": [
                {"action": "collect_links", "ok": False, "failure_type": "recognition_failure", "detail": {"error": "no_links_collected"}},
                {"action": "extract_page", "ok": False, "failure_type": "execution_failure", "detail": {"error": "unexpected_error: boom"}},
                {"action": "search_web", "ok": False, "failure_type": "planning_failure", "detail": {"error": "dynamic_plan_failed"}},
            ],
            "report": {},
            "memory": {},
        }
        metrics = summarize_metrics(run_result)
        self.assertEqual(metrics["recognition_failure_rate"], 1 / 3)
        self.assertEqual(metrics["planning_failure_rate"], 1 / 3)
        self.assertEqual(metrics["execution_failure_rate"], 1 / 3)

    def test_build_report_exposes_failure_analysis_rows(self) -> None:
        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")
        artifact = build_report(
            workflow,
            {"evidence": []},
            [
                {
                    "action": "collect_links",
                    "ok": False,
                    "failure_type": "recognition_failure",
                    "detail": {"error": "no_links_collected", "fields": {}},
                },
                {
                    "action": "extract_page",
                    "ok": False,
                    "failure_type": "execution_failure",
                    "detail": {"error": "unexpected_error: boom", "fields": {}},
                },
            ],
        )
        failure_row = next(item for item in artifact.failure_analysis if item["failure_type"] == "recognition_failure")
        self.assertEqual(failure_row["count"], 1)


class MarketComparisonTests(unittest.TestCase):
    def test_market_comparison_exposes_advantages(self) -> None:
        report = compare_market_profiles("qa_regression")
        self.assertEqual(report["leader"], "Browser Copilot Harness")
        self.assertIn("deterministic_tests", report["our_advantage_capabilities"])
        self.assertEqual(report["best_external"], "OpenAI Operator / ChatGPT agent")


class RequirementSlotSignalTests(unittest.TestCase):
    def test_verify_node_accepts_structured_repo_candidate_signals(self) -> None:
        node = WorkflowNode(
            id="n1",
            type="action",
            instruction="collect repo candidates",
            action="collect_links",
            inputs={"source": "github", "requirement_slot": "repo_candidates"},
        )
        result = ActionResult(
            ok=True,
            action="collect_links",
            url="https://github.com/search?q=browser+agent&type=repositories",
            title="Repository search results",
            text="browser-use stagehand",
            fields={
                "requirement_slot": "repo_candidates",
                "links": [{"text": "browser-use/browser-use", "href": "https://github.com/browser-use/browser-use"}],
                "repo_candidate_signals": {
                    "slot": "repo_candidates",
                    "candidates": [{"text": "browser-use/browser-use", "href": "https://github.com/browser-use/browser-use"}],
                    "query": "browser agent",
                },
            },
        )

        verdict = verify_node(node, result, Observation(url=result.url, title=result.title, text=result.text))

        self.assertTrue(verdict.ok)
        signal_check = next(check for check in verdict.checks if check["name"] == "requirement_slot_signal")
        self.assertTrue(signal_check["pass"])

    def test_verify_node_accepts_structured_repo_metadata_signals_without_keyword_text(self) -> None:
        node = WorkflowNode(
            id="n2",
            type="action",
            instruction="read repository metadata",
            action="deep_read_candidates",
            inputs={"source": "github", "requirement_slot": "repo_metadata"},
        )
        result = ActionResult(
            ok=True,
            action="deep_read_candidates",
            url="https://github.com/search?q=browser+agent&type=repositories",
            title="Repository search results",
            text="opaque content",
            fields={
                "requirement_slot": "repo_metadata",
                "deep_reads": [
                    {
                        "name": "browser-use/browser-use",
                        "url": "https://github.com/browser-use/browser-use",
                        "repo": {"full_name": "browser-use/browser-use", "stars": 12345, "readme_excerpt": "Install and run"},
                    }
                ],
                "repo_metadata_signals": {
                    "slot": "repo_metadata",
                    "repositories": [{"full_name": "browser-use/browser-use", "stars": 12345, "readme_excerpt": "Install and run"}],
                    "readings": [{"name": "browser-use/browser-use"}],
                    "doc_coverage": 1,
                },
            },
        )

        verdict = verify_node(node, result, Observation(url=result.url, title=result.title, text=result.text))

        self.assertTrue(verdict.ok)
        signal_check = next(check for check in verdict.checks if check["name"] == "requirement_slot_signal")
        self.assertTrue(signal_check["pass"])

    def test_verify_node_rejects_missing_structured_signal_for_repo_metadata(self) -> None:
        node = WorkflowNode(
            id="n3",
            type="action",
            instruction="read repository metadata",
            action="deep_read_candidates",
            inputs={"source": "github", "requirement_slot": "repo_metadata"},
        )
        result = ActionResult(
            ok=True,
            action="deep_read_candidates",
            url="https://github.com/search?q=browser+agent&type=repositories",
            title="Repository search results",
            text="plain page text only",
            fields={"requirement_slot": "repo_metadata", "deep_reads": []},
            evidence=[],
        )

        verdict = verify_node(node, result, Observation(url=result.url, title=result.title, text=result.text))

        self.assertFalse(verdict.ok)
        signal_check = next(check for check in verdict.checks if check["name"] == "requirement_slot_signal")
        self.assertFalse(signal_check["pass"])


class ReportBuilderTests(unittest.TestCase):
    def test_build_report_exposes_requirement_progression(self) -> None:
        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")
        memory_dump = {
            "evidence": [
                {
                    "evidence_id": "e1",
                    "source_type": "github",
                    "source_url": "https://github.com/browser-use/browser-use",
                    "claim": "Candidate link: browser-use/browser-use",
                    "support": "browser state automation repo",
                    "confidence": 0.8,
                    "metadata": {},
                }
            ]
        }
        steps = [
            {
                "action": "collect_links",
                "ok": True,
                "detail": {
                    "url": "https://github.com/search?q=browser+automation+agent&type=repositories",
                    "text": "repository search page",
                    "fields": {
                        "source": "github",
                        "requirement_slot": "repo_candidates",
                        "repo_candidate_signals": {"summary": "collected 5 repository candidates"},
                        "links": [{"text": "browser-use/browser-use", "href": "https://github.com/browser-use/browser-use"}],
                    },
                },
            },
            {
                "action": "deep_read_candidates",
                "ok": True,
                "detail": {
                    "url": "https://github.com/browser-use/browser-use",
                    "text": "README install examples",
                    "fields": {
                        "source": "github",
                        "requirement_slot": "repo_metadata",
                        "repo_metadata_signals": {"summary": "stars, forks, license and readme captured"},
                    },
                },
            },
        ]

        artifact = build_report(workflow, memory_dump, steps)

        self.assertTrue(artifact.requirement_progression)
        self.assertEqual(artifact.requirement_progression[0]["requirement_slot"], "repo_candidates")
        self.assertIn("collected 5 repository candidates", artifact.requirement_progression[0]["evidence_summary"])
        self.assertIn("made partial progress", artifact.summary)

    def test_build_report_does_not_claim_completed_when_requirement_slots_missing(self) -> None:
        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")
        memory_dump = {
            "evidence": [
                {
                    "evidence_id": "e1",
                    "source_type": "github",
                    "source_url": "https://github.com/browser-use/browser-use",
                    "claim": "Candidate link: browser-use/browser-use",
                    "support": "browser automation repo",
                    "confidence": 0.8,
                    "metadata": {},
                }
            ]
        }
        steps = [
            {
                "action": "collect_links",
                "ok": True,
                "detail": {
                    "url": "https://github.com/search?q=browser+automation+agent&type=repositories",
                    "text": "repository search page",
                    "fields": {
                        "source": "github",
                        "requirement_slot": "repo_candidates",
                        "repo_candidate_signals": {"summary": "collected repository candidates"},
                        "links": [{"text": "browser-use/browser-use", "href": "https://github.com/browser-use/browser-use"}],
                    },
                },
            }
        ]

        artifact = build_report(workflow, memory_dump, steps)

        self.assertNotIn("completed for", artifact.summary)
        self.assertIn("requirement coverage is still incomplete", artifact.summary)
        self.assertTrue(any("repo_metadata" in item for item in artifact.next_actions))

    def test_build_report_claims_completed_only_when_requirement_slots_are_satisfied(self) -> None:
        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")
        memory_dump = {
            "evidence": [
                {
                    "evidence_id": "e1",
                    "source_type": "github",
                    "source_url": "https://github.com/browser-use/browser-use",
                    "claim": "Candidate link: browser-use/browser-use",
                    "support": "browser automation repo",
                    "confidence": 0.8,
                    "metadata": {},
                }
            ]
        }
        steps = [
            {
                "action": "collect_links",
                "ok": True,
                "detail": {
                    "url": "https://github.com/search?q=browser+automation+agent&type=repositories",
                    "text": "repository search page",
                    "fields": {
                        "source": "github",
                        "requirement_slot": "repo_candidates",
                        "repo_candidate_signals": {"summary": "collected repository candidates"},
                        "links": [{"text": "browser-use/browser-use", "href": "https://github.com/browser-use/browser-use"}],
                    },
                },
            },
            {
                "action": "deep_read_candidates",
                "ok": True,
                "detail": {
                    "url": "https://github.com/browser-use/browser-use",
                    "text": "README install examples",
                    "fields": {
                        "source": "github",
                        "requirement_slot": "repo_metadata",
                        "repo_metadata_signals": {"summary": "stars, forks, language and readme captured"},
                    },
                },
            },
            {
                "action": "extract_page",
                "ok": True,
                "detail": {
                    "url": "https://github.com/browser-use/browser-use",
                    "text": "implementation docs and examples",
                    "fields": {
                        "source": "github",
                        "requirement_slot": "implementation_docs",
                        "implementation_doc_signals": {"summary": "install, run and usage entrypoints captured"},
                    },
                },
            },
            {
                "action": "extract_page",
                "ok": True,
                "detail": {
                    "url": "https://github.com/browser-use/browser-use",
                    "text": "comparison with other browser agents",
                    "fields": {
                        "source": "general",
                        "requirement_slot": "ecosystem_comparison",
                        "comparison_signals": {"summary": "compared with stagehand and other browser agents"},
                    },
                },
            },
        ]

        artifact = build_report(workflow, memory_dump, steps)

        self.assertIn("completed for", artifact.summary)
        self.assertIn("satisfied 4/4 requirement slots", artifact.summary)
        self.assertEqual(artifact.next_actions, [])

    def test_llm_workflow_strategy_prefers_requirement_progression(self) -> None:
        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")
        workflow.nodes.extend(
            [
                WorkflowNode(
                    id="d1",
                    type="agent_dynamic",
                    instruction="抽取候选仓库",
                    action="collect_links",
                    inputs={"source": "github", "requirement_slot": "repo_candidates"},
                ),
                WorkflowNode(
                    id="d2",
                    type="agent_dynamic",
                    instruction="如果当前页无路可走再搜索",
                    action="search_web",
                    inputs={"source": "github", "requirement_slot": "repo_metadata", "query": "browser automation agent github"},
                ),
            ]
        )

        strategy = _workflow_strategy(workflow)

        self.assertTrue(strategy["requirement_progression"])
        self.assertEqual(strategy["requirement_progression"][0]["requirement_slot"], "repo_candidates")
        self.assertEqual(strategy["evidence_plan"][0]["evidence_hint"], "browser automation agent github")
        self.assertEqual(strategy["evidence_plan"][0]["query"], "browser automation agent github")
        self.assertEqual(strategy["search_plan"][0]["query"], "browser automation agent github")

    def test_build_report_exposes_evidence_plan_alias(self) -> None:
        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")
        workflow.nodes.extend(
            [
                WorkflowNode(
                    id="d1",
                    type="agent_dynamic",
                    instruction="如果当前页无路可走再搜索",
                    action="search_web",
                    inputs={"source": "github", "requirement_slot": "repo_candidates", "query": "browser automation agent github"},
                )
            ]
        )

        artifact = build_report(workflow, {"evidence": []}, [])

        self.assertTrue(artifact.evidence_plan)
        self.assertEqual(artifact.evidence_plan[0]["requirement_slot"], "repo_candidates")
        self.assertEqual(artifact.evidence_plan[0]["evidence_hint"], "browser automation agent github")
        self.assertEqual(artifact.evidence_plan[0]["query"], "browser automation agent github")

    def test_evidence_checklist_is_requirement_slot_first(self) -> None:
        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")

        checklist = evidence_checklist(workflow)

        self.assertEqual(checklist[0]["requirement_slot"], "repo_candidates")
        self.assertEqual(checklist[1]["requirement_slot"], "repo_metadata")
        self.assertTrue(checklist[0]["example_query"])

    def test_contextual_checklist_prefers_structured_slot_signals_over_keywords(self) -> None:
        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")
        observation = Observation(
            url="https://github.com/browser-use/browser-use",
            title="browser-use repo",
            text="opaque page body",
        )
        step_outputs = [
            {
                "action": "deep_read_candidates",
                "ok": True,
                "detail": {
                    "url": "https://github.com/browser-use/browser-use",
                    "fields": {
                        "source": "github",
                        "requirement_slot": "repo_metadata",
                        "repo_metadata_signals": {"summary": "stars, forks and license captured"},
                    },
                },
            }
        ]

        checklist = contextual_evidence_checklist(workflow, observation, {"evidence": [], "traces": []}, step_outputs)
        slot_row = next(item for item in checklist if item["requirement_slot"] == "repo_metadata")

        self.assertEqual(slot_row["status"], "satisfied")
        self.assertIn("结构化执行结果", slot_row["evidence"])

    def test_preferred_stage_for_page_uses_structured_partial_trace(self) -> None:
        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")
        observation = Observation(
            url="https://github.com/browser-use/browser-use",
            title="browser-use repo",
            text="opaque page body",
        )
        memory_dump = {
            "evidence": [],
            "traces": [
                {
                    "node": {"action": "deep_read_candidates", "inputs": {"requirement_slot": "repo_metadata"}},
                    "output": {"fields": {"requirement_slot": "repo_metadata", "repo_metadata_signals": {"summary": "metadata captured"}}},
                    "verdict": {"ok": True},
                }
            ],
        }

        preferred = preferred_stage_for_page(workflow, observation, memory_dump, [])

        self.assertEqual(preferred, "repo_metadata")

    def test_stage_visible_on_current_page_prefers_extracted_fields(self) -> None:
        observation = Observation(
            url="https://github.com/browser-use/browser-use",
            title="browser-use repo",
            text="opaque body",
            extracted_fields={
                "requirement_slot": "repo_metadata",
                "repo_metadata_signals": {"summary": "stars and license captured"},
            },
        )

        visible = stage_visible_on_current_page("repo_metadata", "opaque body", observation)

        self.assertTrue(visible)

    def test_stage_present_in_evidence_prefers_observation_structured_fields(self) -> None:
        observation = Observation(
            url="https://github.com/browser-use/browser-use",
            title="browser-use repo",
            text="opaque body",
            extracted_fields={
                "requirement_slot": "implementation_docs",
                "implementation_doc_signals": {"summary": "README and install docs captured"},
            },
        )

        present = stage_present_in_evidence("implementation_docs", "", observation)

        self.assertTrue(present)

    def test_stage_affinity_score_prefers_structured_fields_over_text_bias(self) -> None:
        observation = Observation(
            url="https://github.com/search?q=browser+automation+agent&type=repositories",
            title="Repository search results",
            text="generic text",
            extracted_fields={
                "requirement_slot": "repo_metadata",
                "repo_metadata_signals": {"summary": "stars and license captured"},
            },
        )

        metadata_score = _stage_affinity_score("repo_metadata", observation)
        candidate_score = _stage_affinity_score("repo_candidates", observation)

        self.assertGreater(metadata_score, candidate_score)

    def test_stage_policy_module_matches_navigator_affinity_behavior(self) -> None:
        observation = Observation(
            url="https://github.com/browser-use/browser-use",
            title="browser-use repo",
            text="generic text only",
            extracted_fields={"requirement_slot": "repo_metadata", "repo_metadata_signals": {"summary": "captured repo stats"}},
        )

        navigator_score = _stage_affinity_score("repo_metadata", observation)
        policy_score = policy_stage_affinity_score("repo_metadata", observation, looks_like_results_page=False, has_searchbox=False)

        self.assertEqual(navigator_score, policy_score)

    def test_stage_visible_soft_scoring_keeps_repo_candidates_on_results_page(self) -> None:
        observation = Observation(
            url="https://github.com/search?q=browser+automation+agent&type=repositories",
            title="Repository search results",
            text="generic text",
            elements=[{"text": "browser-use/browser-use", "href": "https://github.com/browser-use/browser-use"}],
        )

        visible = stage_visible_on_current_page("repo_candidates", "generic text", observation)

        self.assertTrue(visible)

    def test_stage_visible_soft_scoring_prefers_structured_metadata_without_exact_keywords(self) -> None:
        observation = Observation(
            url="https://github.com/browser-use/browser-use",
            title="browser-use repo",
            text="generic text only",
            extracted_fields={"requirement_slot": "repo_metadata", "repo_metadata_signals": {"summary": "captured repo stats"}},
        )

        visible = stage_visible_on_current_page("repo_metadata", "generic text only", observation)

        self.assertTrue(visible)

    def test_requirement_driven_query_is_minimal_and_slot_specific(self) -> None:
        query = requirement_driven_query("推荐1000元以内降噪耳机", "shopping", "comparative_reviews")

        self.assertEqual(query, "1000元以内降噪耳机 评测 对比")

    def test_agent_step_context_exposes_page_fingerprint_and_slot_state(self) -> None:
        workflow = plan_goal("调研浏览器自动化智能体仓库", Observation(url="https://github.com", title="", text=""), domain="github")
        observation = Observation(
            url="https://github.com/search?q=browser+automation+agent&type=repositories",
            title="Repository search results",
            text="browser-use stagehand",
            elements=[{"text": "browser-use/browser-use", "href": "https://github.com/browser-use/browser-use"}],
        )

        context = build_agent_step_context(workflow, observation, {"evidence": [], "traces": []}, [], 1)

        self.assertEqual(context.priority_requirement_slot, "repo_candidates")
        self.assertEqual(context.page_fingerprint.url, observation.url)
        self.assertEqual(context.current_page_capabilities["has_candidate_links"], True)


if __name__ == "__main__":
    unittest.main()
