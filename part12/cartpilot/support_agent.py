"""
Part 8 — human-in-the-loop for refunds.

ADK's Tool Confirmation flow (introduced in 1.14, carried into 2.0, and
still marked experimental in the docs) lets a tool pause and wait for a
person to approve it before it actually runs. In `adk web`, this renders
as an approval dialog in the browser. Small refunds process
automatically; anything above our threshold pauses for a human.
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext
from google.adk.tools.agent_tool import AgentTool
from pydantic import BaseModel, Field

RETURN_POLICY = (
    "Items can be returned within 30 days of delivery if unused and in "
    "original packaging. Refunds are issued to the original payment method "
    "within 5-7 business days of us receiving the return."
)

REFUND_APPROVAL_THRESHOLD = 50.00


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
order_status_task = AgentTool(agent=order_status_agent)


async def refund_requires_approval(amount: float, tool_context: ToolContext) -> bool:
    """Refunds at or below the threshold auto-approve; larger ones need a human."""
    return amount > REFUND_APPROVAL_THRESHOLD


def process_refund(order_id: str, amount: float, reason: str, tool_context: ToolContext) -> dict:
    """Processes a refund for a previous order.

    Args:
        order_id: The order to refund, e.g. "CP-10234".
        amount: The refund amount in dollars.
        reason: A short reason for the refund (e.g. "damaged item").
    """
    # By the time this body runs, ADK has already handled the pause/approval
    # dance for amounts over the threshold — if we're executing at all,
    # either the amount was auto-approved or a human approved it.
    # In production this calls the real payments/refunds system.
    return {
        "status": "success",
        "order_id": order_id,
        "refunded_amount": amount,
        "reason": reason,
        "message": f"Refunded ${amount:.2f} for order {order_id}.",
    }


# require_confirmation accepts a function of the tool's own arguments (plus
# ToolContext), evaluated before the tool runs. Under the threshold, the
# tool executes immediately with no pause at all.
refund_tool = FunctionTool(process_refund, require_confirmation=refund_requires_approval)

support_agent = Agent(
    model="gemini-3.5-flash",
    name="support_agent",
    description=(
        "Specialist for order status, returns, refunds, and policy questions. "
        "Delegate here for anything post-purchase or policy-related."
    ),
    instruction="""
You handle CartPilot support questions.
- Use `get_return_policy` for policy questions.
- Use `order_status_task` for order tracking (needs an order_id).
- Use `process_refund` to issue refunds. Always confirm the order_id,
  amount, and reason with the shopper before calling it. If the amount
  is large, tell the shopper it may need manager approval and could
  take a moment.
- Be empathetic but concise.
""",
    tools=[get_return_policy, order_status_task, refund_tool],
)
