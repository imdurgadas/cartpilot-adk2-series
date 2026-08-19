"""
Part 2 — giving the search agent real tools.
ADK turns typed Python functions into function-calling tools automatically:
the function name, docstring, type hints, and parameter names all become
part of the schema the model sees. Write them like you're documenting a
public API, because you are.
"""

# Google ADK agent framework and tool context
from google.adk.agents import Agent
from google.adk.tools import ToolContext

# Local product catalog data and lookup helpers
from .catalog import find_products, get_product



def search_products(query: str, category: str, tool_context: ToolContext) -> dict:
    """Searches the CartPilot catalog for products.

    Args:
        query: Free-text search term, e.g. "water bottle". Pass an empty
            string to browse by category only.
        category: Optional category filter, e.g. "outdoor", "electronics",
            "apparel". Pass an empty string to search all categories.

    Returns:
        A dict with a "results" list of matching products, each including
        sku, name, price, and stock count.
    """
    # ToolContext is injected by ADK — never document it in the docstring,
    # the model never sees it as a parameter it needs to fill in.
    results = find_products(query=query, category=category)
    # Remember the last search in session state so a follow-up like
    # "add the second one" can be resolved without re-searching — see Part 3.
    tool_context.state["last_search_results"] = [r["sku"] for r in results]
    return {"status": "success", "results": results}


def get_product_details(sku: str) -> dict:
    """Fetches full details for a single product by SKU.

    Args:
        sku: The product SKU, e.g. "sku-002".

    Returns:
        A dict with the product's details, or a status of "not_found"
        if the SKU doesn't exist.
    """
    product = get_product(sku)
    if product is None:
        return {"status": "not_found", "sku": sku}
    return {"status": "success", "product": product}


root_agent = Agent(
    model="gemini-2.5-flash",
    name="product_search_agent",
    description=(
        "Helps shoppers find products in the CartPilot store by name, "
        "category, or general description."
    ),
    instruction="""
You are the CartPilot product search assistant.

- Use `search_products` to find items matching what the shopper describes.
- Use `get_product_details` when the shopper wants more info on one item.
- If `search_products` returns no results, say so plainly and suggest
  broadening the search (drop the category filter, try a different term).
- Don't call a tool more than once for the same query — read the results
  you already have before deciding you need another search.
- Keep responses short (2-4 sentences).
""",
    tools=[search_products, get_product_details],
)

# --- Sample Execution Output ---
# User: "Do you have any water bottles?"
# Tool Call: search_products(query="water bottle", category="")
# Tool Output: {"status": "success", "results": [{"sku": "sku-002", "name": "Insulated Water Bottle 1L", "category": "outdoor", "price": 24.5, "stock": 42, "color": "steel", "sizes": ["one-size"]}]}
# State Update: {"last_search_results": ["sku-002"]}
# Agent (product_search_agent): "We have the Insulated Water Bottle 1L in steel for $24.50 (42 currently in stock). Would you like more details or help adding it to your order?"

