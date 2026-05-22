from __future__ import annotations

import unittest

from unittest.mock import patch

from agent_py.web_app import create_app


class ExtensionApiTest(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.app = create_app()
        except RuntimeError as exc:  # pragma: no cover
            self.skipTest(str(exc))
        self.client = self.app.test_client()

    def test_health_endpoint(self) -> None:
        response = self.client.get("/api/extension/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["service"], "python-browser-agent")
        self.assertIn("llmDefaultSource", data)

    def test_plan_endpoint_returns_plan(self) -> None:
        payload = {
            "task": "搜索 多模态大模型",
            "observation": {
                "url": "https://example.com",
                "title": "Example Search",
                "text": "搜索 多模态大模型",
                "elements": [
                    {
                        "id": "e1",
                        "tag": "input",
                        "role": "searchbox",
                        "label": "搜索",
                        "placeholder": "搜索主题",
                        "name": "q",
                        "visible": True,
                        "enabled": True,
                        "bbox": {"x": 1, "y": 1, "width": 100, "height": 20},
                    },
                    {
                        "id": "e2",
                        "tag": "button",
                        "role": "button",
                        "text": "搜索",
                        "label": "搜索",
                        "visible": True,
                        "enabled": True,
                        "bbox": {"x": 1, "y": 25, "width": 60, "height": 20},
                    },
                ],
            },
            "settings": {
                "useLlm": False,
                "backendUrl": "http://127.0.0.1:8787",
            },
        }
        response = self.client.post("/api/extension/plan", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertIn(data["source"], {"python-rule", "python-llm"})
        self.assertIn("llmRequested", data)
        self.assertIn("llmEnabled", data)
        self.assertEqual(data["plan"]["actions"][0]["type"], "type")
        self.assertIn("controller", data)
        self.assertIn("taskQueue", data["controller"])
        self.assertIn("parallelBranches", data["controller"])

    def test_recommendation_task_requires_llm_and_fails_closed(self) -> None:
        payload = {
            "task": "帮我推荐一款耳机",
            "observation": {
                "url": "https://example.com",
                "title": "Example Products",
                "text": "推荐 耳机",
                "elements": [],
            },
            "settings": {
                "useLlm": True,
            },
        }
        with patch("agent_py.web_app.try_plan_with_llm", side_effect=RuntimeError("invalid_grant")):
            response = self.client.post("/api/extension/plan", json=payload)
        self.assertEqual(response.status_code, 409)
        data = response.get_json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["taskMode"], "recommendation")
        self.assertTrue(data["llmRequired"])
        self.assertEqual(data["failureCode"], "llm_invalid_grant")

    def test_recommend_endpoint_persists_json_and_returns_result(self) -> None:
        payload = {
            "task": "帮我推荐一款耳机",
            "observation": {
                "url": "https://example.com/search",
                "title": "耳机搜索",
                "text": "耳机 推荐",
                "cards": [
                    {"title": "耳机A", "summary": "降噪 蓝牙", "price": "¥399", "rating": "4.7", "href": "https://example.com/a"},
                    {"title": "耳机B", "summary": "音质 续航", "price": "¥499", "rating": "4.8", "href": "https://example.com/b"},
                ],
                "elements": [],
            },
            "execution": {"logs": [{"type": "collect", "ok": True}]},
            "settings": {"useLlm": True},
        }
        llm_json = (
            '{"comparisonTable":[{"title":"耳机A","price":"¥399","sound":"良好","performance":"稳定","comfort":"舒适","battery":"30h","score":8.9,"reason":"价格与体验平衡","url":"https://example.com/a"}],'
            '"topPick":"耳机A","why":"预算内综合表现最好","evidence":["https://example.com/a"],"confidence":0.86}'
        )
        with patch("agent_py.comparison.request_text_completion", return_value=llm_json):
            response = self.client.post("/api/extension/recommend", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("artifactPath", data)
        self.assertEqual(data["recommendation"]["topPick"], "耳机A")


if __name__ == "__main__":
    unittest.main()
