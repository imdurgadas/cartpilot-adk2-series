# Google ADK agent framework, sequential pipelines, tool context, and AgentTool wrapper
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

# Local product catalog data and structured order confirmation schema
from .catalog import get_product
from .schemas import OrderConfirmation


CART_KEY = "cart"
DISCOUNT_CODES = {"SAVE10": 0.10, "WELCOME5": 0.05}


def add_to_cart(sku: str, quantity: int, tool_context: ToolContext) -> dict:
    """Adds a product to the cart.

    Args:
        sku: The product SKU to add.
        quantity: How many units to add.
    """
    product = get_product(sku)
    if product is None:
        return {"status": "not_found", "sku": sku}
    if product["stock"] < quantity:
        return {"status": "insufficient_stock", "available": product["stock"]}
    cart = tool_context.state.get(CART_KEY, [])
    for line in cart:
        if line["sku"] == sku:
            line["quantity"] += quantity
            break
    else:
        cart.append({"sku": sku, "quantity": quantity})
    tool_context.state[CART_KEY] = cart
    return {"status": "success", "cart": cart}


def view_cart(tool_context: ToolContext) -> dict:
    """Returns current cart contents with line totals."""
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


def validate_cart(tool_context: ToolContext) -> dict:
    """Checks every cart item against current stock levels."""
    cart = tool_context.state.get(CART_KEY, [])
    if not cart:
        return {"status": "invalid", "issues": ["Cart is empty."]}
    issues = [f"Only {get_product(e['sku'])['stock']} left of {get_product(e['sku'])['name']}."
              for e in cart if get_product(e["sku"]) and get_product(e["sku"])["stock"] < e["quantity"]]
    return {"status": "invalid" if issues else "valid", "issues": issues}


def apply_discount_code(tool_context: ToolContext) -> dict:
    """Applies a discount code (if provided) to the cart subtotal."""
    code = (tool_context.state.get("discount_code") or "").upper()
    cart = tool_context.state.get(CART_KEY, [])
    subtotal = sum(get_product(e["sku"])["price"] * e["quantity"] for e in cart if get_product(e["sku"]))
    rate = DISCOUNT_CODES.get(code, 0.0)
    discount_amount = round(subtotal * rate, 2)
    return {"status": "success", "subtotal": round(subtotal, 2), "discount_code": code or None,
            "discount_amount": discount_amount, "net_subtotal": round(subtotal - discount_amount, 2)}


validation_agent = Agent(model="gemini-2.5-flash", name="cart_validation_agent",
    description="Validates cart contents against stock before checkout.",
    instruction="Call `validate_cart` and report its result exactly as returned.",
    tools=[validate_cart], output_key="validation_result")

discount_agent = Agent(model="gemini-2.5-flash", name="discount_agent",
    description="Applies any discount code to the cart subtotal.",
    instruction="Validation: {validation_result}\nCall `apply_discount_code` and report the result.",
    tools=[apply_discount_code], output_key="pricing_result")

checkout_step_agent = Agent(model="gemini-2.5-flash", name="checkout_step_agent",
    description="Produces the final structured order confirmation.",
    instruction="""
Pricing result: {pricing_result}
Compute estimated_tax as 8% of net_subtotal, total as net_subtotal + tax,
an order_id like "CP-12345", and a friendly shopper_message.
""",
    output_schema=OrderConfirmation, output_key="order_confirmation")

checkout_pipeline = SequentialAgent(
    name="checkout_pipeline",
    description="Runs cart validation, pricing, and order confirmation in order.",
    sub_agents=[validation_agent, discount_agent, checkout_step_agent],
)

# AgentTool vs sub_agents: sub_agents hand full conversational control to
# the child (the coordinator steps aside); AgentTool lets an agent call
# another agent the way it calls a function — get a result back, keep
# control itself. We use AgentTool here so cart_agent can invoke the
# checkout pipeline as one step in a larger cart-management conversation,
# rather than permanently transferring the conversation away from it.
checkout_tool = AgentTool(agent=checkout_pipeline)

cart_agent = Agent(
    model="gemini-2.5-flash",
    name="cart_agent",
    description=(
        "Specialist for managing the shopper's cart: adding/removing items, "
        "viewing the cart, and running checkout. Delegate here for anything "
        "cart- or order-related."
    ),
    instruction="""
You manage the shopper's cart. Use `add_to_cart`, `view_cart`.
When the shopper confirms they want to complete the purchase, call the
`checkout_pipeline` tool and relay its order_confirmation to them clearly.
""",
    tools=[add_to_cart, view_cart, checkout_tool],
)

# --- Sample Output ---
# add_to_cart("sku-001", 1, ctx) -> {"status": "success", "cart": [{"sku": "sku-001", "quantity": 1}]}
# view_cart(ctx) -> {"status": "success", "lines": [{"sku": "sku-001", "name": "Trail Runner Jacket", "quantity": 1, "line_total": 89.99}], "subtotal": 89.99}

