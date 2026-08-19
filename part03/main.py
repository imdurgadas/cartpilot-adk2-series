"""
Part 3 — a plain-Python console runner, so we can see session state
persist across turns without going through `adk web`.
`adk web` and `adk run` do this same Runner/SessionService wiring for
you under the hood; this file exists purely to make it visible.
"""

# Standard library asyncio for asynchronous event loop
import asyncio

# Google ADK runtime and in-memory session management
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Local cart agent instance
from cartpilot_cart.agent import root_agent


APP_NAME = "cartpilot"
USER_ID = "demo-user"


async def main():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

    turns = [
        "Do you have any water bottles?",
        "Add one to my cart.",
        "What's in my cart so far?",
    ]

    for turn in turns:
        print(f"\n> {turn}")
        message = types.Content(role="user", parts=[types.Part(text=turn)])
        async for event in runner.run_async(user_id=USER_ID, session_id=session.id, new_message=message):
            if event.is_final_response() and event.content and event.content.parts:
                print(event.content.parts[0].text)

    # Inspect raw state directly — this is what the model is reading
    # each turn, not the full conversation transcript.
    final_session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=session.id)
    print("\n--- raw session state ---")
    print(final_session.state)


if __name__ == "__main__":
    asyncio.run(main())

# --- Console Run Output ---
# > Do you have any water bottles?
# Yes! We have the Insulated Water Bottle 1L available for $24.50. We currently have 42 in stock. Would you like to add one to your cart?
#
# > Add one to my cart.
# Added 1x Insulated Water Bottle 1L to your cart. Your subtotal is now $24.50.
#
# > What's in my cart so far?
# You have 1x Insulated Water Bottle 1L in your cart with a subtotal of $24.50.
#
# --- raw session state ---
# {'cart': [{'sku': 'sku-002', 'quantity': 1}]}

