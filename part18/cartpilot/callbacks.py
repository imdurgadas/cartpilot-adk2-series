"""
Part 11 — guardrails and observability via ADK's six callback hooks.

    before_agent -> before_model -> [LLM call] -> after_model
        -> (if tool call) before_tool -> [tool runs] -> after_tool -> back to before_model
    -> after_agent

Each hook can either observe (return None, execution continues normally)
or override (return a value, which short-circuits the step it guards).
This is also where structured audit logging belongs — e.g. every refund
approval from Part 8 should leave a trail here, not just in application
logs, because "who approved what, and when" is a compliance question,
not a debugging convenience.

Note: ADK's docs recommend Plugins over per-agent Callbacks for policies
that should apply globally across every agent in a system, since a
Plugin attaches once at the Runner level instead of being copy-pasted
onto every agent. We use Callbacks here because they're simpler to
follow for a single tutorial; consider Plugins for CartPilot's real
production guardrail layer.
"""

import logging
import time

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

logger = logging.getLogger("cartpilot.audit")
logging.basicConfig(level=logging.INFO)

BLOCKED_TERMS = {"ignore previous instructions", "system prompt"}  # minimal example


def log_request_start(callback_context: CallbackContext):
    """before_agent_callback: structured start-of-turn logging."""
    count = callback_context.state.get("request_count", 0) + 1
    callback_context.state["request_count"] = count
    logger.info("agent_start agent=%s turn=%d", callback_context.agent_name, count)
    return None  # None = continue normally


def block_prompt_injection(callback_context: CallbackContext, llm_request: LlmRequest):
    """before_model_callback: a minimal guardrail example. Real systems
    should use a proper classifier here, not a substring blocklist —
    this is illustrative of the HOOK, not a production-grade filter."""
    last_text = ""
    if llm_request.contents:
        last = llm_request.contents[-1]
        if last.parts:
            last_text = (last.parts[0].text or "").lower()

    if any(term in last_text for term in BLOCKED_TERMS):
        logger.warning("blocked_request agent=%s reason=policy", callback_context.agent_name)
        # Returning an LlmResponse here skips the actual model call entirely —
        # zero tokens spent on a request we're not going to honor anyway.
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="I can't help with that request.")],
            )
        )
    return None


def audit_tool_call(tool: BaseTool, args: dict, tool_context: ToolContext):
    """before_tool_callback: logs every tool invocation with its
    arguments before it runs — this is the audit trail Part 8's refund
    approvals need. Returning None lets the call proceed unmodified."""
    logger.info("tool_call tool=%s args=%s", tool.name, args)
    return None


def audit_tool_result(tool: BaseTool, args: dict, tool_context: ToolContext, tool_response: dict | None):
    """after_tool_callback: logs the outcome. For sensitive tools like
    `process_refund`, this line IS the audit record of what happened."""
    status = (
        tool_response.get("status", "success")
        if isinstance(tool_response, dict)
        else ("success" if tool_response is not None else "completed")
    )
    logger.info("tool_result tool=%s status=%s", tool.name, status)
    return None  # None = use the tool's actual response unmodified


def log_request_end(callback_context: CallbackContext):
    """after_agent_callback: closes out the structured log line for this turn."""
    logger.info("agent_end agent=%s", callback_context.agent_name)
    return None


def attach_standard_callbacks(agent) -> None:
    """Applies the shared guardrail/observability callback set to an agent.
    A thin helper so we don't repeat five assignments per agent."""
    agent.before_agent_callback = log_request_start
    agent.before_model_callback = block_prompt_injection
    agent.before_tool_callback = audit_tool_call
    agent.after_tool_callback = audit_tool_result
    agent.after_agent_callback = log_request_end

# --- Callback Audit Logs ---
# INFO:cartpilot.audit:agent_start agent=cartpilot_coordinator turn=1
# INFO:cartpilot.audit:tool_call tool=search_products args={'query': 'jacket', 'category': ''}
# INFO:cartpilot.audit:tool_result tool=search_products status=success
# INFO:cartpilot.audit:agent_end agent=cartpilot_coordinator
#
# Prompt Injection Intercept:
# WARNING:cartpilot.audit:blocked_request agent=cartpilot_coordinator reason=policy
# Agent: "I can't help with that request."

