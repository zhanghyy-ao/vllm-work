from __future__ import annotations

from browser_agent.browser.action import BrowserSession, execute_action
from browser_agent.types import Action, ActionResult, Observation, WorkflowNode


def dispatch(action: Action, observation: Observation):
    """Single entrypoint for tool execution."""
    return execute_action(action, observation)


def dispatch_node(session: BrowserSession, node: WorkflowNode, observation: Observation) -> ActionResult:
    """Execute one workflow node inside an existing browser session."""
    return session.execute(node, observation)
