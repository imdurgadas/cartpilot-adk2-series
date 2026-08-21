"""
Part 7 — the Task API: delegating a bounded unit of work to a single-turn
task agent, instead of a full conversational sub-agent hand-off.

`mode` is a new ADK 2.0 surface (confirmed via ADK's public GitHub
discussions, still evolving at time of writing — check the current
adk.dev docs before relying on it in production):

- mode="chat"        (default for a sub-agent): full multi-turn
                       conversation with the user.
- mode="task"  (default for a workflow node): does its job in one
                       shot with no back-and-forth, given structured
                       input, producing structured output. No chat.
- mode="task"         : like single_turn, but can hold a short back-and-
                       forth WITH the user to gather what it needs before
                       finishing — useful for something like "collect
                       return details" without becoming a full specialist.

We use single_turn here: "what's the status of order X" needs zero
conversation — it's a lookup, not a dialogue.
"""

# Google ADK agent framework and AgentTool wrapper
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

# Pydantic schema validation for task input/output contracts
from pydantic import BaseModel, Field


RETURN_POLICY = (
    "Items can be returned within 30 days of delivery if unused and in "
    "original packaging. Refunds are issued to the original payment method "
    "within 5-7 business days of us receiving the return. Sale items are "
    "final unless defective."
)


def get_return_policy() -> dict:
    """Returns CartPilot's current return and refund policy text."""
    return {"status": "success", "policy": RETURN_POLICY}


def get_order_status(order_id: str) -> dict:
    """Looks up the status of a previous order.

    Args:
        order_id: The order reference, e.g. "CP-10234".
    """
    return {"status": "success", "order_id": order_id, "state": "shipped",
            "estimated_delivery": "2-3 business days"}


class OrderStatusRequest(BaseModel):
    order_id: str = Field(description="The order reference to look up.")


class OrderStatusResult(BaseModel):
    order_id: str
    state: str
    estimated_delivery: str
    summary: str = Field(description="One friendly sentence summarizing status for the shopper.")


# A single-turn task agent: structured in, structured out, no conversation.
# This is deliberately the cheapest possible shape for a bounded lookup —
# one model call, fixed input, fixed output, done.
order_status_agent = Agent(
    model="gemini-3.5-flash",
    name="order_status_agent",
    mode="task",
    description="Looks up and summarizes a single order's status. Non-conversational.",
    instruction="Call `get_order_status` with the given order_id and write a one-line friendly summary.",
    tools=[get_order_status],
    input_schema=OrderStatusRequest,
    output_schema=OrderStatusResult,
)

# AgentTool is the reliable way to invoke a single_turn task agent from
# another agent today: support_agent calls it, gets a structured
# OrderStatusResult back, and stays in control of the conversation —
# no conversational hand-off, no transfer_to_agent.
order_status_task = AgentTool(agent=order_status_agent)

support_agent = Agent(
    model="gemini-3.5-flash",
    name="support_agent",
    description=(
        "Specialist for order status, returns, and refund policy questions. "
        "Delegate here for anything post-purchase or policy-related."
    ),
    instruction="""
You handle CartPilot support questions.
- Use `get_return_policy` for return/refund policy questions.
- For order tracking, call `order_status_task` with the order_id — don't
  try to answer status questions from memory or guesswork. Ask the
  shopper for their order ID if missing.
- Be empathetic but concise. Don't promise anything the policy doesn't state.
""",
    tools=[get_return_policy, order_status_task],
)

# --- Single-Turn Task Delegation Output ---
# User: "Where is order CP-90124?"
# support_agent invokes order_status_task(order_id="CP-90124")
# order_status_agent produces OrderStatusResult:
# {
#     "order_id": "CP-90124",
#     "state": "shipped",
#     "estimated_delivery": "2-3 business days",
#     "summary": "Your order CP-90124 has shipped and is expected to arrive in 2-3 business days."
# }
# support_agent relays: "Your order CP-90124 has shipped and is estimated to arrive in 2-3 business days. Let me know if you need anything else!"

