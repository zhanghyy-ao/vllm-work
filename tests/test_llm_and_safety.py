from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from agent_py.comparison import generate_comparison
from agent_py.llm_planner import LLMConfig, parse_plan, plan_with_llm
from agent_py.observer import observe_html
from agent_py.safety import sanitize_plan
from agent_py.schema import Action, Plan


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "demo-site" / "index.html").read_text(encoding="utf-8")


class LLMAndSafetyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.observation = observe_html(HTML, "http://127.0.0.1:8765")

    def test_parse_plain_json_plan(self) -> None:
        plan = parse_plan('{"summary":"ok","confidence":0.9,"warnings":[],"actions":[{"type":"summarize","reason":"test"}]}')
        self.assertEqual(plan.summary, "ok")
        self.assertEqual(plan.actions[0].type, "summarize")

    def test_parse_markdown_json_plan(self) -> None:
        plan = parse_plan('```json\n{"summary":"ok","confidence":0.7,"actions":[{"type":"copy","reason":"test"}]}\n```')
        self.assertEqual(plan.actions[0].type, "copy")

    def test_parse_invalid_json_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_plan("not json")

    def test_sanitize_drops_invalid_action_type(self) -> None:
        plan = Plan("bad", 0.1, [Action("eval_js", reason="bad")])
        clean = sanitize_plan(plan, self.observation)
        self.assertEqual(clean.actions, [])
        self.assertTrue(clean.warnings)

    def test_sanitize_drops_missing_target(self) -> None:
        plan = Plan("bad", 0.1, [Action("click", target_id="e999", reason="bad")])
        clean = sanitize_plan(plan, self.observation)
        self.assertEqual(clean.actions, [])
        self.assertIn("targetId", clean.warnings[0])

    def test_high_risk_click_becomes_highlight(self) -> None:
        submit = next(element for element in self.observation.elements if "提交" in element.haystack())
        plan = Plan("submit", 0.9, [Action("click", target_id=submit.id, reason="提交表单")])
        clean = sanitize_plan(plan, self.observation)
        self.assertEqual(clean.actions[0].type, "highlight")
        self.assertEqual(clean.actions[0].risk_level, "high")
        self.assertTrue(clean.actions[0].requires_confirmation)

    def test_high_risk_send_becomes_highlight(self) -> None:
        send = next(element for element in self.observation.elements if "发送" in element.haystack())
        plan = Plan("send", 0.9, [Action("click", target_id=send.id, reason="发送消息")])
        clean = sanitize_plan(plan, self.observation)
        self.assertEqual(clean.actions[0].type, "highlight")

    def test_search_submit_is_not_blocked(self) -> None:
        search = next(element for element in self.observation.elements if "搜索" in element.haystack() and element.role == "button")
        plan = Plan("search", 0.9, [Action("click", target_id=search.id, reason="点击搜索按钮")])
        clean = sanitize_plan(plan, self.observation)
        self.assertEqual(clean.actions[0].type, "click")

    def test_explicit_submit_can_be_allowed(self) -> None:
        submit = next(element for element in self.observation.elements if "提交" in element.haystack())
        plan = Plan("submit", 0.9, [Action("click", target_id=submit.id, reason="用户明确要求提交表单")])
        clean = sanitize_plan(plan, self.observation, allow_explicit_submit=True)
        self.assertEqual(clean.actions[0].type, "click")

    def test_hard_risk_still_blocked_when_explicit_allowed(self) -> None:
        submit = next(element for element in self.observation.elements if "提交" in element.haystack())
        plan = Plan("pay", 0.9, [Action("click", target_id=submit.id, reason="用户明确要求付款")])
        clean = sanitize_plan(plan, self.observation, allow_explicit_submit=True)
        self.assertEqual(clean.actions[0].type, "highlight")

    def test_gemini_model_on_synai_uses_native_endpoint(self) -> None:
        config = LLMConfig(
            api_base="https://synai996.space/v1",
            api_key="test-key",
            model="gemini-3-flash",
        )

        with patch("agent_py.llm_planner._post_json") as post_json:
            post_json.return_value = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"summary":"ok","confidence":0.8,"warnings":[],"actions":[{"type":"summarize","reason":"test"}]}'
                                }
                            ]
                        }
                    }
                ]
            }

            plan = plan_with_llm("总结当前页面", self.observation, config)

        args, _kwargs = post_json.call_args
        self.assertIn("/v1beta/models/gemini-3-flash:generateContent", args[0])
        self.assertEqual(plan.actions[0].type, "summarize")

    def test_explicit_gemini_base_uses_native_endpoint(self) -> None:
        config = LLMConfig(
            api_base="https://generativelanguage.googleapis.com",
            api_key="test-key",
            model="gemini-2.5-flash",
        )

        with patch("agent_py.llm_planner._post_json") as post_json:
            post_json.return_value = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"summary":"ok","confidence":0.8,"warnings":[],"actions":[{"type":"summarize","reason":"test"}]}'
                                }
                            ]
                        }
                    }
                ]
            }

            plan = plan_with_llm("总结当前页面", self.observation, config)

        args, kwargs = post_json.call_args
        self.assertIn("/v1beta/models/gemini-2.5-flash:generateContent", args[0])
        self.assertFalse(kwargs["include_auth"])
        self.assertEqual(plan.actions[0].type, "summarize")

    def test_compare_can_use_openai_compatible_llm(self) -> None:
        config = LLMConfig(
            api_base="https://synai996.space/v1",
            api_key="test-key",
            model="vllm-compare",
        )
        with patch("agent_py.comparison.request_text_completion") as request_text_completion:
            request_text_completion.return_value = (
                '{"focus":"浏览器智能体","winner":"Browser Harness","summary":"更适合工程化。",'
                '"ranking":[{"title":"Browser Harness","reason":"CDP 与 skills 更完整","score":9.4,"price":"¥0","rating":"4.7","date":"","features":["CDP","skills"]}]}'
            )
            artifact = generate_comparison("比较这些浏览器智能体方案", self.observation, llm_config=config)
        self.assertIn("LLM 总结", artifact)
        self.assertIn("Browser Harness", artifact)
        self.assertIn("CDP", artifact)


if __name__ == "__main__":
    unittest.main()
