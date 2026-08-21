# Google ADK agent framework
from google.adk.agents import Agent

# Observability callbacks, cost tracking, and specialist sub-agents
from .callbacks import attach_standard_callbacks
from .cart_agent import cart_agent
from .cost_tracking import track_token_usage
from .search_agent import search_agent
from .support_agent import support_agent


for _agent in (search_agent, cart_agent, support_agent):
    attach_standard_callbacks(_agent)
    _agent.after_model_callback = track_token_usage

root_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="cartpilot_coordinator",
    description="CartPilot's main coordinator agent.",
    instruction="""
You are CartPilot's coordinator. Delegate to the right specialist:
- Product discovery -> search_agent
- Cart actions and checkout -> cart_agent
- Orders, returns, policy questions -> support_agent
Greet the shopper on their first message, then delegate.
""",
    sub_agents=[search_agent, cart_agent, support_agent],
    after_model_callback=track_token_usage,
)
attach_standard_callbacks(root_agent)

# --- Sample Multi-Agent Output with MCP Shipping ---
# User: "How much is shipping to ZIP 94105 for my cart?"
# Coordinator -> delegates to cart_agent
# cart_agent -> get_shipping_rate(destination_zip="94105", weight_lbs=2.5) [via MCP toolset]
# Response: "Estimated shipping to 94105 is $10.88 with delivery in 3-5 business days."

