from __future__ import annotations

from browser_agent.browser.action import execute_action
from browser_agent.types import Action, Observation


def dispatch(action: Action, observation: Observation):
    """Single entrypoint for tool execution."""
    return execute_action(action, observation)
