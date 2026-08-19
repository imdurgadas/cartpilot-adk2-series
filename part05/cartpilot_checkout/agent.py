"""
Part 5 — checkout as an explicit graph, not an implicit conversation.

Instead of trusting one LLM to "remember" to validate stock, then apply
a discount, then confirm the order, in the right order, every time,
we express the pipeline as a SequentialAgent of narrow, single-purpose
sub-agents. Each step writes its result to session state via
`output_key`; the next step reads it via `{placeholder}` interpolation
in its instruction. Order is guaranteed by the graph, not by hoping the
model calls things correctly.
"""

# Google ADK agent framework, sequential workflow pipelines, and tool context
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import ToolContext

# Local product lookup helper and structured output schemas
from .catalog import get_product
from .schemas import OrderConfirmation


CART_KEY = "cart"
DISCOUNT_CODES = {"SAVE10": 0.10, "WELCOME5": 0.05}


def validate_cart(tool_context: ToolContext) -> dict:
    """Checks every item in the cart against current stock levels."""
    cart = tool_context.state.get(CART_KEY, [])
    if not cart:
        return {"status": "invalid", "issues": ["Cart is empty."]}
    issues = []
    for entry in cart:
        product = get_product(entry["sku"])
        if product is None:
            issues.append(f"{entry['sku']} no longer exists.")
        elif product["stock"] < entry["quantity"]:
            issues.append(f"Only {product['stock']} left of {product['name']}.")
    return {"status": "invalid" if issues else "valid", "issues": issues}


def apply_discount_code(tool_context: ToolContext) -> dict:
    """Applies a discount code (if the shopper provided one) to the cart subtotal."""
    code = (tool_context.state.get("discount_code") or "").upper()
    cart = tool_context.state.get(CART_KEY, [])
    subtotal = sum(get_product(e["sku"])["price"] * e["quantity"] for e in cart if get_product(e["sku"]))
    rate = DISCOUNT_CODES.get(code, 0.0)
    discount_amount = round(subtotal * rate, 2)
    return {
        "status": "success",
        "subtotal": round(subtotal, 2),
        "discount_code": code or None,
        "discount_amount": discount_amount,
        "net_subtotal": round(subtotal - discount_amount, 2),
    }


# --- Step 1: pure validation. Cheap model, narrow job, no ambiguity. ---
validation_agent = Agent(
    model="gemini-2.5-flash",
    name="cart_validation_agent",
    description="Validates cart contents against stock before checkout.",
    instruction="Call `validate_cart` and report its result exactly as returned.",
    tools=[validate_cart],
    output_key="validation_result",
)

# --- Step 2: pricing/discount logic. Also narrow, also cheap. ---
discount_agent = Agent(
    model="gemini-2.5-flash",
    name="discount_agent",
    description="Applies any discount code to the cart subtotal.",
    instruction="""
Validation result so far: {validation_result}
Call `apply_discount_code` and report its result exactly as returned.
""",
    tools=[apply_discount_code],
    output_key="pricing_result",
)

# --- Step 3: the only step that produces the shopper-facing artifact. ---
checkout_agent = Agent(
    model="gemini-2.5-flash",
    name="checkout_agent",
    description="Produces the final structured order confirmation.",
    instruction="""
Pricing result: {pricing_result}

Using net_subtotal from the pricing result:
- Compute estimated_tax as 8% of net_subtotal, rounded to 2 decimals.
- Compute total as net_subtotal + estimated_tax.
- Generate order_id as "CP-" followed by a 5-digit number.
- Write a friendly one-line shopper_message. Mention the discount if
  discount_amount > 0.
""",
    output_schema=OrderConfirmation,
    output_key="order_confirmation",
)

# The graph: validate -> price -> confirm. Deterministic order,
# regardless of what any individual step's model decides to do.
checkout_pipeline = SequentialAgent(
    name="checkout_pipeline",
    description="Runs cart validation, pricing, and confirmation in order.",
    sub_agents=[validation_agent, discount_agent, checkout_agent],
)

root_agent = Agent(
    model="gemini-2.5-flash",
    name="cartpilot_agent",
    description="CartPilot shopping assistant with a deterministic checkout pipeline.",
    instruction="""
You are the CartPilot shopping assistant.
When the shopper wants to check out, transfer to `checkout_pipeline`.
Otherwise, chat normally and help them with their cart.
""",
    sub_agents=[checkout_pipeline],
)

# --- Sequential Pipeline Execution Trace ---
# 1. cart_validation_agent -> validate_cart()
#    State: validation_result={"status": "valid", "issues": []}
# 2. discount_agent -> apply_discount_code()
#    State: pricing_result={"status": "success", "subtotal": 89.99, "discount_code": "SAVE10", "discount_amount": 9.0, "net_subtotal": 80.99}
# 3. checkout_agent -> OrderConfirmation (Structured Output)
#    State: order_confirmation={
#        "order_id": "CP-48201",
#        "lines": [{"sku": "sku-001", "name": "Trail Runner Jacket", "quantity": 1, "line_total": 89.99}],
#        "subtotal": 80.99,
#        "estimated_tax": 6.48,
#        "total": 87.47,
#        "shopper_message": "Order CP-48201 confirmed! Your 10% discount was applied."
#    }

