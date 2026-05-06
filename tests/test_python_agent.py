from __future__ import annotations

import json
import unittest
from pathlib import Path

from agent_py import BrowserHarness, observe_html, plan_task
from agent_py.memory import AgentMemory
from agent_py.runner import BrowserAgentRunner
from agent_py.schema import Action, Plan


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "demo-site" / "index.html").read_text(encoding="utf-8")
URL = "http://127.0.0.1:8765"


class PythonBrowserAgentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.observation = observe_html(HTML, URL)

    def run_task(self, command: str) -> BrowserHarness:
        plan = plan_task(command, self.observation)
        harness = BrowserHarness(self.observation)
        result = harness.run(plan)
        self.assertTrue(result.ok, command)
        self.assertGreater(len(result.logs), 0, command)
        return harness

    def test_observer_collects_page_state(self) -> None:
        self.assertIn("Browser Agent Demo Site", self.observation.title)
        self.assertGreaterEqual(len(self.observation.elements), 10)
        self.assertGreaterEqual(len(self.observation.cards), 4)
        self.assertGreaterEqual(len(self.observation.tables), 1)
        self.assertIn("agent-demo@sysu.example", self.observation.emails)
        self.assertTrue(any(link["text"] == "WebVoyager" for link in self.observation.links))

    def test_search_skill(self) -> None:
        harness = self.run_task("搜索 多模态大模型")
        self.assertTrue(any(value == "多模态大模型" for value in harness.values.values()))
        self.assertIn("多模态大模型", harness.artifact)
        self.assertIn("自动搜索结果", harness.artifact)

    def test_search_uses_search_button_not_submit_form(self) -> None:
        plan = plan_task("搜索 多模态大模型", self.observation)
        click_actions = [action for action in plan.actions if action.type == "click"]
        if click_actions:
            target = next(element for element in self.observation.elements if element.id == click_actions[0].target_id)
            self.assertIn("搜索", target.haystack())
            self.assertNotIn("提交表单", target.haystack())

    def test_realtime_question_uses_web_search(self) -> None:
        plan = plan_task("今天的天气怎么样", self.observation)
        self.assertEqual(plan.actions[0].type, "navigate")
        self.assertIn("bing.com/search", plan.actions[0].value)
        self.assertTrue(any(action.type == "extract" for action in plan.actions))

    def test_runner_completes_llm_search_plan_with_extraction(self) -> None:
        partial = Plan(
            "search",
            0.9,
            [
                Action("type", target_id="e1", value="多模态大模型", reason="输入关键词"),
                Action("click", target_id="e2", reason="点击搜索"),
            ],
        )
        completed = BrowserAgentRunner()._complete_plan("搜索 多模态大模型", partial)
        self.assertEqual([action.type for action in completed.actions[-2:]], ["extract", "copy"])
        self.assertEqual(completed.actions[-2].value, "多模态大模型")

    def test_form_fill_skill(self) -> None:
        harness = self.run_task("填写 姓名=张三 邮箱=zhangsan@example.com 主题=多模态智能体 备注=这是课程 Demo")
        filled = set(harness.values.values())
        self.assertIn("张三", filled)
        self.assertIn("zhangsan@example.com", filled)
        self.assertIn("多模态智能体", filled)
        self.assertIn("这是课程 Demo", filled)
        self.assertGreaterEqual(len(harness.highlighted), 1)

    def test_form_fill_keeps_topic_inside_form_context(self) -> None:
        plan = plan_task("填写 姓名=张三 邮箱=zhangsan@example.com 主题=多模态智能体 备注=这是课程 Demo", self.observation)
        topic_action = next(action for action in plan.actions if action.value == "多模态智能体")
        topic_target = next(element for element in self.observation.elements if element.id == topic_action.target_id)
        self.assertEqual(topic_target.label, "主题")
        self.assertEqual(topic_target.form_id, "profileForm")

    def test_reply_skill(self) -> None:
        harness = self.run_task("回复小明：我今晚八点前把材料发你")
        self.assertIn("我今晚八点前把材料发你", set(harness.values.values()))
        self.assertGreaterEqual(len(harness.highlighted), 1)

    def test_summarize_skill(self) -> None:
        harness = self.run_task("总结当前页面")
        self.assertIn("页面摘要", harness.artifact)
        self.assertIn("浏览器辅助操作智能体测试站", harness.artifact)
        self.assertEqual(harness.clipboard, harness.artifact)

    def test_collect_contacts_skill(self) -> None:
        harness = self.run_task("提取页面链接和邮箱")
        data = json.loads(harness.artifact)
        self.assertEqual(data["kind"], "contacts")
        self.assertIn("agent-demo@sysu.example", data["emails"])
        self.assertTrue(any(item["text"] == "Nanobrowser" for item in data["links"]))
        self.assertEqual(harness.clipboard, harness.artifact)

    def test_collect_prices_skill(self) -> None:
        harness = self.run_task("抽取价格")
        data = json.loads(harness.artifact)
        self.assertEqual(data["kind"], "prices")
        self.assertIn("¥0", data["items"])

    def test_collect_tables_skill(self) -> None:
        harness = self.run_task("导出表格")
        data = json.loads(harness.artifact)
        self.assertEqual(data["kind"], "tables")
        self.assertEqual(data["items"][0][0], ["功能", "任务数", "指标"])

    def test_collect_cards_skill(self) -> None:
        harness = self.run_task("结构化抽取结果卡片")
        data = json.loads(harness.artifact)
        self.assertEqual(data["kind"], "cards")
        self.assertTrue(any(item["title"] == "Browser Harness" for item in data["items"]))

    def test_compare_skill(self) -> None:
        harness = self.run_task("比较这些浏览器智能体方案")
        self.assertIn("综合比较", harness.artifact)
        self.assertIn("候选数量", harness.artifact)
        self.assertIn("Browser Harness", harness.artifact)
        self.assertIn("推荐", harness.artifact)
        self.assertIn("来源：", harness.artifact)

    def test_compare_plan_searches_when_page_lacks_relevant_candidates(self) -> None:
        plan = plan_task("比较 RTX 4090 和 RTX 4080", self.observation)
        self.assertEqual([action.type for action in plan.actions[:3]], ["type", "click", "collect"])
        self.assertEqual(plan.actions[-2].type, "compare")
        self.assertEqual(plan.actions[-1].type, "copy")

    def test_compare_uses_memory_context(self) -> None:
        memory = AgentMemory(task="比较浏览器智能体")
        memory.search_queries.append("browser agent tools")
        memory.candidate_snapshots.append(
            {
                "url": "https://example.com/search",
                "title": "search",
                "cards": [
                    {
                        "title": "AgentOps Browser",
                        "summary": "评分 4.8，适合可观测性分析。",
                        "href": "https://example.com/agentops",
                    }
                ],
            }
        )
        harness = BrowserHarness(self.observation, memory=memory)
        result = harness.run(plan_task("比较这些浏览器智能体方案", self.observation))
        self.assertTrue(result.ok)
        self.assertIn("记忆上下文", harness.artifact)
        self.assertIn("browser agent tools", harness.artifact)

    def test_compare_renders_detail_sampling_and_recommendation_reason(self) -> None:
        memory = AgentMemory(task="比较浏览器智能体")
        memory.remember_detail_page(
            {"title": "Browser Harness", "href": "https://github.com/browser-use/browser-harness"},
            self.observation,
            metadata={
                "about": "Self-healing harness for LLM web tasks.",
                "capabilities": ["Playwright browser control", "multi-step automation"],
                "install": ["pip install browser-harness"],
            },
        )
        harness = BrowserHarness(self.observation, memory=memory)
        result = harness.run(plan_task("比较这些浏览器智能体方案", self.observation))
        self.assertTrue(result.ok)
        self.assertIn("详情页采样", harness.artifact)
        self.assertIn("综合数据表", harness.artifact)
        self.assertIn("最终推荐理由", harness.artifact)
        self.assertIn("Self-healing harness", harness.artifact)

    def test_ui_analysis_skill(self) -> None:
        harness = self.run_task("分析这个界面能做什么")
        self.assertIn("界面分析", harness.artifact)
        self.assertIn("可交互元素", harness.artifact)
        self.assertIn("搜索/检索信息", harness.artifact)
        self.assertIn("需要谨慎确认的按钮", harness.artifact)

    def test_project_analysis_skill(self) -> None:
        harness = self.run_task("分析这个项目的可复用性")
        self.assertIn("项目分析", harness.artifact)
        self.assertIn("可复用性判断", harness.artifact)
        self.assertIn("Browser Harness", harness.artifact)

    def test_find_on_page_skill(self) -> None:
        harness = self.run_task("帮忙查找 Browser Harness")
        self.assertIn("页面查找", harness.artifact)
        self.assertIn("Browser Harness", harness.artifact)
        self.assertEqual(harness.clipboard, harness.artifact)

    def test_fallback_click_or_extract(self) -> None:
        harness = self.run_task("打开 WebVoyager")
        self.assertTrue(harness.highlighted or harness.artifact)

    def test_open_browser_harness_link_exactly(self) -> None:
        plan = plan_task("打开 Browser Harness", self.observation)
        target_id = plan.actions[0].target_id
        target = next(element for element in self.observation.elements if element.id == target_id)
        self.assertEqual(target.text, "Browser Harness")
        self.assertIn("browser-harness", target.href)


if __name__ == "__main__":
    unittest.main()
