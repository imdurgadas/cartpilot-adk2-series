"""
Part 13 — wiring CartPilot's cart_agent up to the shipping MCP server.

Governance notes baked into this file's comments — the things that
change once a tool comes from a third party instead of your own code:
1. AUTH: this local demo server needs none, but a real shipping
   provider's MCP server would need an API key passed via `env=`,
   scoped as narrowly as that provider's auth model allows.
2. RATE LIMITS: third-party MCP servers have their own rate limits you
   don't control. tool_filter below keeps CartPilot from accidentally
   exposing every tool the server offers — only the one it needs.
3. COST ATTRIBUTION: log every call to a third-party tool the same way
   Part 11 logs internal tool calls, so a shipping-provider bill spike
   is traceable back to which agent/conversation caused it.
"""

# Standard library imports for path manipulation, module shims, and typing
import os
import sys
import types
from datetime import timedelta
from typing import Any, Callable

# Third-party async runtime and Model Context Protocol (MCP) packages
import anyio
import mcp
import mcp.client.streamable_http
import mcp.shared.dispatcher
from mcp import StdioServerParameters
from mcp.server import MCPServer

# --- MCP 2.0 Module Shims for Google ADK McpToolset ---
mcp.client.streamable_http.McpHttpClientFactory = Callable[..., Any]

session_mod = types.ModuleType("mcp.shared.session")
session_mod.ProgressFnT = mcp.shared.dispatcher.ProgressFnT
sys.modules["mcp.shared.session"] = session_mod
mcp.shared.session = session_mod

exc_mod = types.ModuleType("mcp.shared.exceptions")
exc_mod.McpError = mcp.MCPError
sys.modules["mcp.shared.exceptions"] = exc_mod
mcp.shared.exceptions = exc_mod

fastmcp_mod = types.ModuleType("mcp.server.fastmcp")
fastmcp_mod.FastMCP = MCPServer
fastmcp_mod.Context = object
sys.modules["mcp.server.fastmcp"] = fastmcp_mod
mcp.server.fastmcp = fastmcp_mod

import mcp.types
if not hasattr(mcp.types.Tool, "inputSchema"):
    mcp.types.Tool.inputSchema = property(lambda self: getattr(self, "input_schema", None))
if not hasattr(mcp.types.Tool, "outputSchema"):
    mcp.types.Tool.outputSchema = property(lambda self: getattr(self, "output_schema", None))


# Google ADK MCP toolset integration and connection parameter models
from google.adk.tools.mcp_tool import McpToolset
import google.adk.tools.mcp_tool.mcp_session_manager as msm
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

msm.MCPSessionManager._is_session_disconnected = lambda self, session: False

_orig_fail_after = anyio.fail_after
def _fail_after_seconds(delay, *args, **kwargs):
    if isinstance(delay, timedelta):
        delay = delay.total_seconds()
    return _orig_fail_after(delay, *args, **kwargs)
anyio.fail_after = _fail_after_seconds


_SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "mcp_servers", "shipping_server.py")

shipping_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python3",
            args=[_SERVER_SCRIPT],
            # A real provider would need something like:
            # env={"SHIPPING_API_KEY": os.getenv("SHIPPING_API_KEY", "")},
        ),
        timeout=30,
    ),
    # Only expose the one tool CartPilot actually needs, even if the
    # server offers more — narrows both the model's tool list and the
    # attack surface of "what could this connection be used for."
    tool_filter=["get_shipping_rate"],
)

# --- Sample McpToolset Output ---
# McpToolset connects to shipping_server.py via stdio.
# Exposes: ['get_shipping_rate']
# Tool call: get_shipping_rate(destination_zip="98101", weight_lbs=3.0) ->
# {'status': 'success', 'estimated_cost': 11.5, 'delivery_window_days': '3-5'}

