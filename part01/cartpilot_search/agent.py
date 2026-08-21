"""
Part 1 — CartPilot's first agent: a single LlmAgent with no tools yet.
Run it with `adk web` from the parent folder and chat with it in the browser.
"""

# Google ADK agent framework for creating AI agents
from google.adk.agents import Agent


# gemini-2.5-flash-lite is the right default for a customer-facing conversational
# node: low per-token cost, low latency, strong instruction following.
# We'll swap in gemini-2.5-pro later for nodes that need deeper reasoning
# (e.g. resolving ambiguous refund policy questions) — see Part 10.
root_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="product_search_agent",
    description=(
        "Helps shoppers find products in the CartPilot store by name, "
        "category, or general description."
    ),
    instruction="""
You are the CartPilot product search assistant.

- Greet the shopper briefly, then help them find products.
- You do not have real product data yet (that's Part 2) — for now,
  be honest that search isn't wired up, and ask clarifying questions
  about what they're looking for (category, budget, use case).
- Keep responses short (2-4 sentences). Shoppers are on mobile.
""",
)

# --- Sample Execution Output ---
# User: "Hi! Looking for running gear."
# Agent (product_search_agent): "Hello! Welcome to CartPilot. I'd love to help you find running gear, but our search system isn't wired up just yet. Could you share what specific items, budget, or use case you have in mind so I can note them down?"

