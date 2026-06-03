from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class MarketPluginProfile:
    name: str
    category: str
    source_url: str
    updated_on: str
    capabilities: Dict[str, bool]
    strengths: List[str]
    limits: List[str]


OUR_PROFILE = MarketPluginProfile(
    name="Browser Copilot Harness",
    category="homework-harness",
    source_url="local://browser_agent",
    updated_on="2026-06-02",
    capabilities={
        "scenario_templates": True,
        "human_handoff": True,
        "verification_loop": True,
        "audit_trail": True,
        "deterministic_tests": True,
        "market_benchmarking": True,
        "persistent_session": False,
        "multitask_parallel": False,
        "teach_repeat": False,
    },
    strengths=[
        "Scenario routing is explicit and explainable.",
        "Sensitive browser actions stop for approval.",
        "Every run emits steps, events, memory and metrics.",
        "The project ships with deterministic regression tests.",
    ],
    limits=[
        "No live browser session persistence yet.",
        "No multi-tab parallel execution yet.",
    ],
)


MARKET_PROFILES = [
    MarketPluginProfile(
        name="OpenAI Operator / ChatGPT agent",
        category="consumer-agent",
        source_url="https://openai.com/index/introducing-operator/",
        updated_on="2025-01-23",
        capabilities={
            "scenario_templates": False,
            "human_handoff": True,
            "verification_loop": False,
            "audit_trail": False,
            "deterministic_tests": False,
            "market_benchmarking": False,
            "persistent_session": True,
            "multitask_parallel": True,
            "teach_repeat": False,
        },
        strengths=[
            "Strong general web task execution for end users.",
            "Can take over browser tasks with user confirmation.",
        ],
        limits=[
            "Not packaged as a transparent local evaluation harness.",
            "No built-in coursework-style deterministic test suite.",
        ],
    ),
    MarketPluginProfile(
        name="Anthropic computer use",
        category="developer-api",
        source_url="https://www.anthropic.com/news/3-5-models-and-computer-use",
        updated_on="2024-10-22",
        capabilities={
            "scenario_templates": False,
            "human_handoff": True,
            "verification_loop": False,
            "audit_trail": False,
            "deterministic_tests": False,
            "market_benchmarking": False,
            "persistent_session": False,
            "multitask_parallel": False,
            "teach_repeat": False,
        },
        strengths=[
            "Low-level screen, click and keypress control for custom agents.",
            "Good foundation for building browser automation agents.",
        ],
        limits=[
            "Developers must add their own scenario routing and evaluation.",
            "Audit and benchmark layers are left to the integrator.",
        ],
    ),
    MarketPluginProfile(
        name="Browser Use",
        category="developer-framework",
        source_url="https://docs.browser-use.com/",
        updated_on="docs-current",
        capabilities={
            "scenario_templates": False,
            "human_handoff": True,
            "verification_loop": False,
            "audit_trail": False,
            "deterministic_tests": False,
            "market_benchmarking": False,
            "persistent_session": True,
            "multitask_parallel": False,
            "teach_repeat": False,
        },
        strengths=[
            "Strong browser auth and real-session integration.",
            "Useful for extraction and authenticated browser workflows.",
        ],
        limits=[
            "Does not ship a scenario benchmark matrix for coursework.",
            "Verification policy and grading logic are project-specific.",
        ],
    ),
    MarketPluginProfile(
        name="Google Project Mariner",
        category="research-product",
        source_url="https://deepmind.google/technologies/project-mariner/",
        updated_on="2025-05-20",
        capabilities={
            "scenario_templates": False,
            "human_handoff": True,
            "verification_loop": False,
            "audit_trail": False,
            "deterministic_tests": False,
            "market_benchmarking": False,
            "persistent_session": True,
            "multitask_parallel": True,
            "teach_repeat": True,
        },
        strengths=[
            "Strong multi-task and teach-repeat product direction.",
            "Promising high-level consumer agent UX.",
        ],
        limits=[
            "Not an open local harness with explicit grading artifacts.",
            "Harder to inspect or customize for a homework-style demo.",
        ],
    ),
]
