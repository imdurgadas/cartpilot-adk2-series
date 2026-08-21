# Google ADK agent framework
from google.adk.agents import Agent


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
    """Looks up the status of a previous order (mocked for this series).

    Args:
        order_id: The order reference, e.g. "CP-10234".
    """
    # In production this calls the real order-management system.
    return {"status": "success", "order_id": order_id, "state": "shipped",
            "estimated_delivery": "2-3 business days"}


# Support conversations skew toward ambiguous, sometimes emotionally
# charged questions ("this is the second time this happened") where a
# stronger model earns its higher cost. We still default to Flash and
# only escalate specific hard cases to Pro — see Part 10.
support_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="support_agent",
    description=(
        "Specialist for order status, returns, and refund policy questions. "
        "Delegate here for anything post-purchase or policy-related."
    ),
    instruction="""
You handle CartPilot support questions.
- Use `get_return_policy` for return/refund policy questions.
- Use `get_order_status` for order tracking questions (ask for the order ID
  if the shopper hasn't given one).
- Be empathetic but concise. Don't promise anything the policy doesn't state.
- You cannot issue refunds yourself yet — that's coming in Part 8.
""",
    tools=[get_return_policy, get_order_status],
)

# --- Sample Output ---
# get_return_policy() ->
# {"status": "success", "policy": "Items can be returned within 30 days of delivery if unused and in original packaging. Refunds are issued to the original payment method within 5-7 business days of us receiving the return. Sale items are final unless defective."}
# get_order_status("CP-10234") ->
# {"status": "success", "order_id": "CP-10234", "state": "shipped", "estimated_delivery": "2-3 business days"}

