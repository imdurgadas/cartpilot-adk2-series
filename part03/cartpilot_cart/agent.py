"""
Part 3 — session state and a real shopping cart.
Cart contents live in `tool_context.state`, not in conversation text.
That's the key move for keeping token growth under control as a session
gets longer: the model doesn't need to re-read "I added the jacket, then
the socks, then removed the jacket..." on every turn — it reads the
current cart state, which is O(cart size), not O(conversation length).
"""

# Google ADK agent framework and tool context
from google.adk.agents import Agent
from google.adk.tools import ToolContext

# Local product catalog lookup helpers
from .catalog import find_products, get_product


CART_KEY = "cart"  # list[dict] of {sku, qty} stored in session state


def search_products(query: str, category: str) -> dict:
    """Searches the CartPilot catalog for products.

    Args:
        query: Free-text search term. Empty string to browse by category only.
        category: Optional category filter. Empty string to search all.
    """
    return {"status": "success", "results": find_products(query=query, category=category)}


def add_to_cart(sku: str, quantity: int, tool_context: ToolContext) -> dict:
    """Adds a product to the shopper's cart.

    Args:
        sku: The product SKU to add.
        quantity: How many units to add. Must be a positive integer.
    """
    product = get_product(sku)
    if product is None:
        return {"status": "not_found", "sku": sku}
    if quantity <= 0:
        return {"status": "invalid_quantity", "message": "Quantity must be positive."}
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
    """Returns the current contents of the shopper's cart with line totals."""
    cart = tool_context.state.get(CART_KEY, [])
    lines, subtotal = [], 0.0
    for entry in cart:
        product = get_product(entry["sku"])
        if not product:
            continue
        line_total = product["price"] * entry["quantity"]
        subtotal += line_total
        lines.append({
            "sku": entry["sku"], "name": product["name"],
            "quantity": entry["quantity"], "line_total": round(line_total, 2),
        })
    return {"status": "success", "lines": lines, "subtotal": round(subtotal, 2)}


def remove_from_cart(sku: str, tool_context: ToolContext) -> dict:
    """Removes a product entirely from the shopper's cart.

    Args:
        sku: The product SKU to remove.
    """
    cart = tool_context.state.get(CART_KEY, [])
    new_cart = [line for line in cart if line["sku"] != sku]
    if len(new_cart) == len(cart):
        return {"status": "not_in_cart", "sku": sku}
    tool_context.state[CART_KEY] = new_cart
    return {"status": "success", "cart": new_cart}


root_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="cartpilot_agent",
    description="Helps shoppers search products and manage their cart.",
    instruction="""
You are the CartPilot shopping assistant.
- Use `search_products` to help shoppers find items.
- Use `add_to_cart`, `view_cart`, and `remove_from_cart` to manage the cart.
- Always confirm what changed after a cart action (e.g. "Added 2x Trail
  Runner Jacket — your subtotal is now $179.98.").
- Never guess at cart contents — call `view_cart` if you're not sure.
- Keep responses short (2-4 sentences).
""",
    tools=[search_products, add_to_cart, view_cart, remove_from_cart],
)

# --- Sample Execution Output ---
# User: "Add 2 water bottles to my cart."
# Tool Call: add_to_cart(sku="sku-002", quantity=2) -> {"status": "success", "cart": [{"sku": "sku-002", "quantity": 2}]}
# Agent: "Added 2x Insulated Water Bottle 1L to your cart. Your subtotal is now $49.00."
#
# User: "What's in my cart?"
# Tool Call: view_cart() -> {"status": "success", "lines": [{"sku": "sku-002", "name": "Insulated Water Bottle 1L", "quantity": 2, "line_total": 49.0}], "subtotal": 49.0}
# Agent: "You have 2x Insulated Water Bottle 1L in your cart for a subtotal of $49.00."

