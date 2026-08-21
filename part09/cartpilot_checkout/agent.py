# Google ADK agent framework
from google.adk.agents import Agent

# Resilient payment tool with built-in retry budget
from .tools import charge_payment


root_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="checkout_payment_agent",
    description="Handles payment charging during checkout, with resilient error handling.",
    instruction="""
You process payment for CartPilot orders.
- Call `charge_payment` with the order total.
- If the result has status "success", confirm the charge to the shopper
  with the transaction ID.
- If status is "error": apologize briefly, do NOT call `charge_payment`
  again yourself (it already exhausted its own retry budget), and tell
  the shopper their payment method wasn't charged and they can try
  again in a few minutes or use a different payment method.
""",
    tools=[charge_payment],
)

# --- Sample Execution Output ---
# Scenario 1 (Successful charge):
# Agent: "Your payment of $89.99 was processed successfully! Transaction reference: txn_849201."
#
# Scenario 2 (Exhausted retry budget error):
# Agent: "I apologize, but we were unable to process your payment after several attempts due to a temporary network issue. Your payment method has not been charged. Please try again in a few minutes or use a different payment method."

