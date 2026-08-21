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
    after_model_callback=track_token_usage,
)
attach_standard_callbacks(root_agent)

# --- Production Cloud Run Deployment Output ---
# $ adk deploy cloud_run --project=my-gcp-project --region=us-central1 cartpilot
# [✓] Building container image
# [✓] Pushing to Artifact Registry
# [✓] Deploying to Cloud Run service [cartpilot]
# Service URL: https://cartpilot-uc.a.run.app
# Ready for traffic with scale-to-zero enabled.

