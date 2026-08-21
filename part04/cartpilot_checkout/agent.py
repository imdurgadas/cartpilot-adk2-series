"""
Part 4 — guaranteed structured output.

Asking a plain LlmAgent to "reply in JSON" produces text that LOOKS like
JSON most of the time. In production "most of the time" means silent
parse failures downstream. `output_schema` instead forces the model's
final response to validate against a Pydantic model — ADK handles the
constrained generation / validation, you get a typed object out.
"""

# Standard library random for demo order IDs
import random

# Google ADK agent framework and tool context
from google.adk.agents import Agent
from google.adk.tools import ToolContext

# Local product lookup helper and structured output schemas
from .catalog import get_product
from .schemas import OrderConfirmation


CART_KEY = "cart"


def get_cart_summary(tool_context: ToolContext) -> dict:
    """Returns the shopper's current cart as line items with totals,
    for the checkout agent to turn into a structured confirmation."""
    cart = tool_context.state.get(CART_KEY, [])
    lines, subtotal = [], 0.0
    for entry in cart:
        product = get_product(entry["sku"])
        if not product:
            continue
        line_total = round(product["price"] * entry["quantity"], 2)
        subtotal += line_total
        lines.append({"sku": entry["sku"], "name": product["name"],
                       "quantity": entry["quantity"], "line_total": line_total})
    return {"status": "success", "lines": lines, "subtotal": round(subtotal, 2)}


# A checkout agent's job is narrow and final: turn a cart into a
# structured confirmation. output_schema means its ONLY valid response
# shape is an OrderConfirmation — no chit-chat, no markdown, no tool
# calls after this point (output_schema agents can't call further tools
# in the same turn, by design: it's a terminal, typed step).
checkout_agent = Agent(
    model="gemini-3.5-flash",
    name="checkout_agent",
    description="Produces a structured order confirmation from cart contents.",
    instruction="""
You will be given cart line items, a subtotal, and a tax rate context.
Compute estimated_tax as 8% of subtotal, rounded to 2 decimals.
Compute total as subtotal + estimated_tax.
Generate a short order_id like "CP-" followed by a 5-digit number.
Write a friendly one-line shopper_message confirming the order.
""",
    output_schema=OrderConfirmation,
)


def checkout(tool_context: ToolContext) -> dict:
    """Finalizes the order and returns a structured confirmation.
    Call this only after the shopper has explicitly confirmed they
    want to complete the purchase.
    """
    summary = get_cart_summary(tool_context)
    if not summary["lines"]:
        return {"status": "empty_cart"}
    # In Part 6 this becomes a real delegation to checkout_agent as a
    # sub-agent; here we show the shape directly to keep Part 4 focused.
    subtotal = summary["subtotal"]
    tax = round(subtotal * 0.08, 2)
    confirmation = OrderConfirmation(
        order_id=f"CP-{random.randint(10000, 99999)}",
        lines=summary["lines"],
        subtotal=subtotal,
        estimated_tax=tax,
        total=round(subtotal + tax, 2),
        shopper_message="Your CartPilot order is confirmed — thanks for shopping with us!",
    )
    return {"status": "success", "confirmation": confirmation.model_dump()}


root_agent = Agent(
    model="gemini-3.5-flash",
    name="cartpilot_agent",
    description="Helps shoppers manage their cart and check out.",
    instruction="""
You are the CartPilot shopping assistant.
- Use `get_cart_summary` to check the cart before checkout.
- Use `checkout` only after the shopper explicitly confirms they want
  to complete the purchase — always ask "Ready to check out?" first.
- After checkout, relay the shopper_message and the total clearly.
""",
    tools=[get_cart_summary, checkout],
)

# --- Sample Execution Output ---
# User: "I'm ready to complete my purchase."
# Tool Call: checkout()
# Output: {
#     "status": "success",
#     "confirmation": {
#         "order_id": "CP-54219",
#         "lines": [{"sku": "sku-002", "name": "Insulated Water Bottle 1L", "quantity": 1, "line_total": 24.5}],
#         "subtotal": 24.5,
#         "estimated_tax": 1.96,
#         "total": 26.46,
#         "shopper_message": "Your CartPilot order is confirmed — thanks for shopping with us!"
#     }
# }
# Agent: "Your CartPilot order is confirmed — thanks for shopping with us! Order CP-54219 has been placed for a total of $26.46 (including $1.96 tax)."

