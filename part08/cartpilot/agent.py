# Google ADK agent framework
from google.adk.agents import Agent

# Specialist sub-agents in the multi-agent hierarchy
from .cart_agent import cart_agent
from .search_agent import search_agent
from .support_agent import support_agent


root_agent = Agent(
    model="gemini-3.5-flash",
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

# --- Sample Output ---
# User: "I would like a refund of $25 for order CP-10234 because the package was damaged."
# Coordinator -> delegates to support_agent
# support_agent -> process_refund(order_id="CP-10234", amount=25.0, reason="damaged package") [Auto-approved]
# Response: "I have processed a refund of $25.00 for order CP-10234. You will see it on your original payment method in 5-7 business days."

