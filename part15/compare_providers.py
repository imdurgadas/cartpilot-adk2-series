"""
Part 15 (bonus) — run the SAME agent code against every configured
provider back-to-back, so you can see the swap actually working
without editing .env between runs.

Usage:
    python compare_providers.py

Skips any provider whose required credentials/server aren't available
rather than failing the whole run.
"""

# Standard library imports for async execution, OS environment, and module reloading
import asyncio
import importlib
import os

# Third-party environment variable loader
from dotenv import load_dotenv

# Google ADK runners and in-memory session management
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Local agent module for multi-provider comparison reloading
import cartpilot_any_llm.agent as agent_module

load_dotenv()

APP_NAME = "cartpilot_any_llm"
USER_ID = "demo-user"
QUERY = "Do you have anything for hiking under $30?"

PROVIDERS_TO_TRY = ["google", "openai", "anthropic", "ollama"]

_REQUIRED_ENV = {
    "google": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "ollama": None,  # no key required, but Ollama must be running locally
}


async def run_one(provider: str) -> None:
    os.environ["CARTPILOT_MODEL_PROVIDER"] = provider

    required = _REQUIRED_ENV[provider]
    if required and not os.getenv(required):
        print(f"\n--- {provider}: skipped (set {required} in .env to try it) ---")
        return

    # Re-import fresh each time so model_config.get_model() re-reads the
    # provider we just set — Python caches module imports otherwise.
    importlib.reload(agent_module)


    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    runner = Runner(agent=agent_module.root_agent, app_name=APP_NAME, session_service=session_service)

    print(f"\n--- {provider} ---")
    try:
        message = types.Content(role="user", parts=[types.Part(text=QUERY)])
        async for event in runner.run_async(user_id=USER_ID, session_id=session.id, new_message=message):
            if event.is_final_response() and event.content and event.content.parts:
                print(event.content.parts[0].text)
    except Exception as exc:  # noqa: BLE001 - this is a demo script, surface the error plainly
        print(f"(failed: {exc})")


async def main():
    for provider in PROVIDERS_TO_TRY:
        await run_one(provider)


if __name__ == "__main__":
    asyncio.run(main())

# --- Sample Comparison Run Output ---
# $ python compare_providers.py
#
# --- google ---
# We have two great hiking options under $30:
# 1. Insulated Water Bottle 1L - $24.50 (in stock)
# 2. Merino Wool Hiking Socks (3-pack) - $18.75 (in stock)
# Would you like to add either of these to your cart?
#
# --- openai ---
# We have the Merino Wool Hiking Socks (3-pack) for $18.75 and the Insulated Water Bottle 1L for $24.50, both under $30 and in stock!
#
# --- anthropic: skipped (set ANTHROPIC_API_KEY in .env to try it) ---
# --- ollama: skipped (set CARTPILOT_OLLAMA_MODEL_DEFAULT or start ollama) ---

