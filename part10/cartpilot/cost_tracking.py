"""
Part 10 — token economics.

`after_model_callback` fires after every single model call, with the raw
LlmResponse — including `usage_metadata` (prompt/candidate/total token
counts, and cached-token counts if context caching is in play). This is
the hook point for turning "how many tokens did that cost" from a guess
into a measured, per-agent number.

IMPORTANT: the $/1M token figures below are illustrative placeholders,
not current pricing. Always pull live rates from
https://ai.google.dev/gemini-api/docs/pricing before using this for
real budgeting.
"""

# Google ADK callback context and LLM response model
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse


# Illustrative only — check current pricing before using these for real budgets.
PRICE_PER_MILLION_TOKENS = {
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
}

USAGE_LOG_KEY = "usage_log"  # session-state key holding a running list


def track_token_usage(callback_context: CallbackContext, llm_response: LlmResponse) -> None:
    """after_model_callback: records token usage and estimated cost for
    every model call, tagged by which agent made it."""
    if not llm_response.usage_metadata:
        return

    usage = llm_response.usage_metadata
    model = callback_context.agent_name  # tag by agent; map to model below if needed
    prices = PRICE_PER_MILLION_TOKENS.get("gemini-2.5-flash")  # default tier for this demo

    input_tokens = usage.prompt_token_count or 0
    output_tokens = usage.candidates_token_count or 0
    cached_tokens = getattr(usage, "cached_content_token_count", 0) or 0

    # Cached tokens are typically billed at a steep discount versus fresh
    # input tokens — this is the mechanism behind context caching: a
    # system instruction or long tool schema block that's identical
    # across calls can be cached once and re-billed cheaply thereafter.
    billable_input_tokens = max(input_tokens - cached_tokens, 0)
    estimated_cost = (
        billable_input_tokens / 1_000_000 * prices["input"]
        + output_tokens / 1_000_000 * prices["output"]
    )

    entry = {
        "agent": callback_context.agent_name,
        "input_tokens": input_tokens,
        "cached_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": round(estimated_cost, 6),
    }
    log = callback_context.state.get(USAGE_LOG_KEY, [])
    log.append(entry)
    callback_context.state[USAGE_LOG_KEY] = log


def summarize_usage(state: dict) -> dict:
    """Rolls up the per-call usage log into per-agent and total cost —
    call this at the end of a conversation (or periodically) to see
    where the money actually went."""
    log = state.get(USAGE_LOG_KEY, [])
    by_agent: dict[str, dict] = {}
    total_cost = 0.0
    for entry in log:
        agent = entry["agent"]
        bucket = by_agent.setdefault(agent, {"calls": 0, "input_tokens": 0,
                                              "output_tokens": 0, "cost_usd": 0.0})
        bucket["calls"] += 1
        bucket["input_tokens"] += entry["input_tokens"]
        bucket["output_tokens"] += entry["output_tokens"]
        bucket["cost_usd"] += entry["estimated_cost_usd"]
        total_cost += entry["estimated_cost_usd"]
    return {"by_agent": by_agent, "total_calls": len(log), "total_cost_usd": round(total_cost, 6)}

# --- Sample Usage Tracking Summary ---
# summarize_usage(session.state) ->
# {
#     "by_agent": {
#         "cartpilot_coordinator": {"calls": 3, "input_tokens": 1240, "output_tokens": 85, "cost_usd": 0.000585},
#         "search_agent": {"calls": 2, "input_tokens": 920, "output_tokens": 140, "cost_usd": 0.000626},
#         "cart_agent": {"calls": 2, "input_tokens": 1100, "output_tokens": 110, "cost_usd": 0.000605}
#     },
#     "total_calls": 7,
#     "total_cost_usd": 0.001816
# }

