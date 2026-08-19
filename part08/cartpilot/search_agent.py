from google.adk.agents import Agent
from google.adk.tools import ToolContext
from .catalog import find_products, get_product


def search_products(query: str, category: str, tool_context: ToolContext) -> dict:
    """Searches the CartPilot catalog for products.

    Args:
        query: Free-text search term. Empty string to browse by category only.
        category: Optional category filter. Empty string to search all.
    """
    results = find_products(query=query, category=category)
    tool_context.state["last_search_results"] = [r["sku"] for r in results]
    return {"status": "success", "results": results}


def get_product_details(sku: str) -> dict:
    """Fetches full details for a single product by SKU.

    Args:
        sku: The product SKU.
    """
    product = get_product(sku)
    return {"status": "success", "product": product} if product else {"status": "not_found", "sku": sku}


# Routing/search is high-volume, low-ambiguity work — Flash is the right
# call both for cost and for latency (shoppers browsing want fast replies).
search_agent = Agent(
    model="gemini-2.5-flash",
    name="search_agent",
    description=(
        "Specialist for finding products in the CartPilot catalog by name, "
        "category, or description. Delegate here for any product discovery question."
    ),
    instruction="""
You help shoppers find products. Use `search_products` and
`get_product_details`. If nothing matches, say so and suggest
broadening the search. Keep responses short.
""",
    tools=[search_products, get_product_details],
)
