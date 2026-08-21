"""
Part 16 (bonus) — pre-flight token counting for CartPilot agents.

Two ways to count tokens BEFORE spending money on a real call:

1. client.models.count_tokens() — a real (essentially free/very cheap)
   API call that returns an exact count for the target model.
2. genai.LocalTokenizer — fully offline, zero network calls, zero cost,
   good for high-volume estimation (CI checks on instruction length,
   budgeting scripts, this file).

Run: python token_budget.py
"""

# Standard library and third-party environment loaders
import os
import warnings
from dotenv import load_dotenv

# Suppress experimental warning for local tokenizer output cleanliness
warnings.filterwarnings("ignore", message=".*local tokenizer.*")

# Google GenAI SDK and offline tokenizer
from google import genai
from google.genai import types
from google.genai.local_tokenizer import LocalTokenizer

load_dotenv()

# --- CartPilot's actual system instructions, for real measurement ---
SEARCH_AGENT_INSTRUCTION = """
You are the CartPilot product search assistant.
- Use `search_products` to find items matching what the shopper describes.
- Use `get_product_details` when the shopper wants more info on one item.
- If `search_products` returns no results, say so and suggest broadening the search.
- Don't call a tool more than once for the same query.
- Keep responses short (2-4 sentences).
"""

SUPPORT_AGENT_INSTRUCTION = """
You handle CartPilot support questions.
- Use `get_return_policy` for policy questions.
- Use `order_status_task` for order tracking (needs an order_id).
- Use `process_refund` to issue refunds. Always confirm the order_id,
  amount, and reason with the shopper before calling it. If the amount
  is large, tell the shopper it may need manager approval.
- Be empathetic but concise.
"""

MODEL = "gemini-3.5-flash"


def count_offline(text: str) -> int:
    """Zero-cost, zero-network token count — safe to call thousands of
    times (e.g. in a CI check that fails if an instruction grows past
    a budget) without touching the API at all."""
    tokenizer = LocalTokenizer(model_name=MODEL)
    return tokenizer.count_tokens(text).total_tokens


def count_online(client: genai.Client, text: str) -> int:
    """A real API call — use this when you need an exact figure for a
    specific request shape (e.g. including tool schemas or multimodal
    content the local tokenizer can't approximate)."""
    return client.models.count_tokens(model=MODEL, contents=text).total_tokens


def main():
    print("=== Offline (free, no API call) ===")
    for name, text in [("search_agent instruction", SEARCH_AGENT_INSTRUCTION),
                        ("support_agent instruction", SUPPORT_AGENT_INSTRUCTION)]:
        tokens = count_offline(text)
        print(f"{name}: {tokens} tokens  (~{len(text)} chars, ~{len(text)/max(tokens,1):.1f} chars/token)")

    print("\n=== Online (real API call, for comparison) ===")
    if not os.getenv("GOOGLE_API_KEY"):
        print("(skipped: set GOOGLE_API_KEY in .env to run online token count)")
    else:
        try:
            client = genai.Client()
            for name, text in [("search_agent instruction", SEARCH_AGENT_INSTRUCTION)]:
                tokens = count_online(client, text)
                print(f"{name}: {tokens} tokens (verified against the live model)")
        except Exception as exc:  # noqa: BLE001
            print(f"(failed: {exc})")

    print(
        "\nWhy this matters: every one of these tokens is re-sent on EVERY "
        "single call that agent makes — this is the fixed 'instruction tax' "
        "referenced in the TCO calculator (tco_calculator.py). A bloated "
        "instruction isn't a one-time cost; it's a permanent per-call tax."
    )


if __name__ == "__main__":
    main()

# --- Sample Token Counting Output ---
# $ python token_budget.py
# === Offline (free, no API call) ===
# search_agent instruction: 95 tokens  (~378 chars, ~4.0 chars/token)
# support_agent instruction: 99 tokens  (~384 chars, ~3.9 chars/token)
#
# === Online (real API call, for comparison) ===
# search_agent instruction: 96 tokens (verified against the live model)
#
# Why this matters: every one of these tokens is re-sent on EVERY single call that agent makes — this is the fixed 'instruction tax' referenced in the TCO calculator (tco_calculator.py). A bloated instruction isn't a one-time cost; it's a permanent per-call tax.

