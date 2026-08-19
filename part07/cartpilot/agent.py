# Google ADK agent framework
from google.adk.agents import Agent

# Specialist sub-agents in the multi-agent hierarchy
from .cart_agent import cart_agent
from .search_agent import search_agent
from .support_agent import support_agent


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
)

# --- Sample Output ---
# User: "Where is order CP-10234?"
# Coordinator -> delegates to support_agent
# support_agent -> order_status_task(order_id="CP-10234")
# Response: "Your order CP-10234 has shipped and is estimated to arrive in 2-3 business days."

