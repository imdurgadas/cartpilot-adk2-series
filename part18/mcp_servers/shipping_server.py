"""
Part 13 — a tiny local MCP server exposing shipping-rate estimation.

This runs as its own process (ADK's McpToolset starts it via stdio),
completely independent of CartPilot's own codebase — the same way a
real third-party shipping provider's MCP server would be independent
of yours. Run standalone to sanity check it:
    python mcp_servers/shipping_server.py
"""

# Model Context Protocol (MCP) server class for creating FastMCP/MCPServer tools
from mcp.server import MCPServer

mcp = MCPServer("cartpilot-shipping")

# Flat-rate table by first digit of destination ZIP, purely illustrative.
_RATE_TABLE = {"0": 6.50, "1": 7.00, "2": 7.50, "3": 8.00, "4": 6.00,
               "5": 6.50, "6": 7.00, "7": 7.50, "8": 8.50, "9": 9.00}


@mcp.tool()
def get_shipping_rate(destination_zip: str, weight_lbs: float) -> dict:
    """Estimates the shipping cost for a package.

    Args:
        destination_zip: The 5-digit destination ZIP code.
        weight_lbs: Package weight in pounds.

    Returns:
        A dict with the estimated shipping cost and delivery window.
    """
    if not destination_zip or not destination_zip[0].isdigit():
        return {"status": "error", "message": "Invalid ZIP code."}
    base_rate = _RATE_TABLE.get(destination_zip[0], 7.50)
    cost = round(base_rate + max(weight_lbs - 1, 0) * 1.25, 2)
    return {"status": "success", "estimated_cost": cost, "delivery_window_days": "3-5"}


if __name__ == "__main__":
    mcp.run(transport="stdio")

# --- Sample MCPServer Tool Execution ---
# get_shipping_rate(destination_zip="94105", weight_lbs=2.0) ->
# {"status": "success", "estimated_cost": 10.25, "delivery_window_days": "3-5"}
#
# get_shipping_rate(destination_zip="10001", weight_lbs=0.5) ->
# {"status": "success", "estimated_cost": 7.00, "delivery_window_days": "3-5"}

