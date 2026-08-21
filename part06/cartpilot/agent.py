"""
Part 6 — CartPilot becomes a real multi-agent system: a coordinator that
routes to Search, Cart, and Support specialists based on their
`description` fields, rather than one agent with a sprawling toolset
and instruction block trying to do everything.
"""

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
You are CartPilot's coordinator. You don't handle product search, cart
management, or support questions yourself — delegate to the right
specialist based on what the shopper needs:

- Product discovery ("do you have...", "show me...") -> search_agent
- Cart actions and checkout ("add to cart", "what's in my cart",
  "check out") -> cart_agent
- Orders, returns, policy questions -> support_agent

Greet the shopper on their first message, then delegate. Don't try to
answer specialist questions yourself.
""",
    sub_agents=[search_agent, cart_agent, support_agent],
)

# --- Coordinator Multi-Agent Turn Trace ---
# User: "Hi! Do you have hiking socks?"
# Coordinator -> delegates to search_agent
# search_agent -> search_products(query="hiking socks", category="")
# Response: "We have the Merino Wool Hiking Socks (3-pack) in grey for $18.75 (60 in stock). Would you like to add some to your cart?"
#
# User: "Add one pack to my cart."
# Coordinator -> delegates to cart_agent
# cart_agent -> add_to_cart(sku="sku-004", quantity=1)
# Response: "Added 1x Merino Wool Hiking Socks (3-pack) to your cart. Your subtotal is now $18.75."
#
# User: "What is your return policy?"
# Coordinator -> delegates to support_agent
# support_agent -> get_return_policy()
# Response: "Items can be returned within 30 days of delivery if unused and in original packaging. Refunds are issued to the original payment method within 5-7 business days."

