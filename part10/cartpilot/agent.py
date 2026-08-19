"""
Part 10 — same coordinator + specialists from Part 8, now with a cost-
tracking callback attached to every agent, so every model call is
measured rather than assumed.
"""

# Google ADK agent framework
from google.adk.agents import Agent

# Token economics callback and specialist sub-agents
from .cart_agent import cart_agent
from .cost_tracking import track_token_usage
from .search_agent import search_agent
from .support_agent import support_agent


# Attach the same callback to every agent in the tree. In Part 11 we'll
# generalize this into a proper plugin so it doesn't need to be pasted
# onto each agent by hand.
for _agent in (search_agent, cart_agent, support_agent):
    _agent.after_model_callback = track_token_usage

root_agent = Agent(
    model="gemini-2.5-flash",
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

# --- Sample Output ---
# Conversation completed with cost tracking active.
# Total model turns: 5 | Total cost: $0.00132 USD
