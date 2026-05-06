from __future__ import annotations

import unittest
from pathlib import Path

from agent_py import BrowserHarness, observe_html, plan_task


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def observe_fixture(name: str, url: str):
    return observe_html((FIXTURES / name).read_text(encoding="utf-8"), url)


class RealWorldSkillsTest(unittest.TestCase):
    def run_task(self, fixture: str, url: str, command: str) -> BrowserHarness:
        observation = observe_fixture(fixture, url)
        plan = plan_task(command, observation)
        harness = BrowserHarness(observation)
        result = harness.run(plan)
        self.assertTrue(result.ok, command)
        self.assertEqual(harness.clipboard, harness.artifact)
        return harness

    def test_research_search_results_page(self) -> None:
        harness = self.run_task(
            "search_results.html",
            "https://www.bing.com/search?q=browser+agent",
            "研究当前页面",
        )
        self.assertIn("研究简报", harness.artifact)
        self.assertIn("Browser Harness", harness.artifact)
        self.assertIn("Nanobrowser", harness.artifact)
        self.assertIn("下一步建议", harness.artifact)

    def test_github_repo_brief(self) -> None:
        harness = self.run_task(
            "github_repo.html",
            "https://github.com/browser-use/browser-harness",
            "分析这个 GitHub 仓库",
        )
        self.assertIn("GitHub 仓库简报", harness.artifact)
        self.assertIn("browser-use/browser-harness", harness.artifact)
        self.assertIn("Installation", harness.artifact)
        self.assertIn("工程判断", harness.artifact)

    def test_docs_page_brief(self) -> None:
        harness = self.run_task(
            "docs_page.html",
            "https://playwright.dev/docs/screenshots",
            "在文档中找 安装 配置 API",
        )
        self.assertIn("文档页简报", harness.artifact)
        self.assertIn("Installation", harness.artifact)
        self.assertIn("pip install playwright", harness.artifact)
        self.assertIn("API key", harness.artifact)

    def test_english_contact_form_fill(self) -> None:
        observation = observe_fixture("contact_form.html", "https://example.com/contact")
        plan = plan_task("填写 name=Alice email=alice@example.com message=Please send me the demo link", observation)
        harness = BrowserHarness(observation)
        result = harness.run(plan)
        self.assertTrue(result.ok)
        self.assertIn("Alice", set(harness.values.values()))
        self.assertIn("alice@example.com", set(harness.values.values()))
        self.assertIn("Please send me the demo link", set(harness.values.values()))
        self.assertGreaterEqual(len(harness.highlighted), 1)


if __name__ == "__main__":
    unittest.main()
