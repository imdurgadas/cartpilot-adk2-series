"""
Part 15 (bonus) — the Part 2 search agent, unmodified except for one
line: `model=get_model("default")` instead of a hardcoded model string.
Everything else — the tools, the docstrings, the instruction — is
completely unaware of which provider is actually answering.

Run this exact file against Gemini, GPT, Claude, or a fully local
Ollama model just by changing CARTPILOT_MODEL_PROVIDER in .env.
"""

# Google ADK agent framework and tool context
from google.adk.agents import Agent
from google.adk.tools import ToolContext

# Local catalog lookup helpers and provider model selector
from .catalog import find_products, get_product
from .model_config import get_model



def search_products(query: str, category: str, tool_context: ToolContext) -> dict:
    """Searches the CartPilot catalog for products.

    Args:
        query: Free-text search term, e.g. "water bottle". Empty string
            to browse by category only.
        category: Optional category filter, e.g. "outdoor", "electronics",
            "apparel". Empty string to search all categories.
    """
    results = find_products(query=query, category=category)
    tool_context.state["last_search_results"] = [r["sku"] for r in results]
    return {"status": "success", "results": results}


def get_product_details(sku: str) -> dict:
    """Fetches full details for a single product by SKU.

    Args:
        sku: The product SKU, e.g. "sku-002".
    """
    product = get_product(sku)
    return {"status": "success", "product": product} if product else {"status": "not_found", "sku": sku}


root_agent = Agent(
    model=get_model("default"),  # <-- the only line that changed from Part 2
    name="product_search_agent",
    description="Helps shoppers find products by name, category, or description.",
    instruction="""
You are the CartPilot product search assistant.
- Use `search_products` to find items matching what the shopper describes.
- Use `get_product_details` when the shopper wants more info on one item.
- If `search_products` returns no results, say so and suggest broadening the search.
- Keep responses short (2-4 sentences).
""",
    tools=[search_products, get_product_details],
)

# --- Sample Output ---
# Running product_search_agent with CARTPILOT_MODEL_PROVIDER="google"
# User: "Do you have water bottles?"
# Response: "Yes, we have the Insulated Water Bottle 1L for $24.50 in stock (42 available). Would you like to add one to your cart?"

