from google.adk.agents import Agent

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
- Orders, returns, refunds, policy questions -> support_agent
Greet the shopper on their first message, then delegate.
""",
    sub_agents=[search_agent, cart_agent, support_agent],
)
attach_standard_callbacks(root_agent)
root_agent.after_model_callback = track_token_usage

# --- Sample Multi-Agent Output with Eval-Tested Coordinator ---
# User: "I'm looking for trail gear under $50"
# Coordinator -> delegates to search_agent
# search_agent -> search_products(query="trail", category="outdoor")
# Response: "We have the Insulated Water Bottle 1L for $24.50 and Compact Camp Stove for $45.00, both in stock and under $50."

