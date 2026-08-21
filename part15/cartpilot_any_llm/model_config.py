"""
Part 15 (bonus) — provider-agnostic model selection.

ADK is model-agnostic by design. An agent's `model` field accepts either:
  (a) a native Gemini model string ("gemini-3.5-flash"), talked to
      directly through the Gemini API, or
  (b) a `LiteLlm` instance, which routes through LiteLLM's unified API
      to any of 100+ providers — OpenAI, Anthropic, Azure, Bedrock,
      Vertex, Ollama, vLLM, and more.

Nothing else about the agent changes: same tools, same output_schema,
same callbacks, same multi-agent structure from every earlier part in
this series. Only the reasoning engine underneath is swappable.

Set CARTPILOT_MODEL_PROVIDER in .env to switch: google | openai |
anthropic | ollama. "ollama" runs fully on your own machine with zero
calls to any cloud API.
"""

# Standard library os for reading environment variables
import os

# Google ADK LiteLlm provider wrapper for multi-LLM routing
from google.adk.models.lite_llm import LiteLlm


_MODEL_IDS = {
    "google": {
        "default": "gemini-3.5-flash",
        "strong": "gemini-2.5-pro",
    },
    "openai": {
        "default": "openai/gpt-4o-mini",
        "strong": "openai/gpt-4o",
    },
    "anthropic": {
        "default": "anthropic/claude-haiku-4-5",
        "strong": "anthropic/claude-sonnet-4-5",
    },
    "ollama": {
        # ollama_chat/ (not ollama/) is the recommended LiteLLM provider
        # prefix — it maps onto Ollama's native chat API and gives more
        # reliable tool-calling behavior than the older ollama/ prefix.
        "default": f"ollama_chat/{os.getenv('CARTPILOT_OLLAMA_MODEL_DEFAULT', 'llama3.2')}",
        "strong": f"ollama_chat/{os.getenv('CARTPILOT_OLLAMA_MODEL_STRONG', 'qwen2.5:14b')}",
    },
}


def get_model(tier: str = "default"):
    """Returns a model reference for the requested tier, honoring
    CARTPILOT_MODEL_PROVIDER. Native Gemini strings pass through as-is;
    every other provider is wrapped in LiteLlm.

    Args:
        tier: "default" (cheap/fast) or "strong" (more capable) — the
            same two-tier convention CartPilot has used since Part 1.
    """
    provider = os.getenv("CARTPILOT_MODEL_PROVIDER", "google").lower()
    if provider not in _MODEL_IDS:
        raise ValueError(
            f"Unknown CARTPILOT_MODEL_PROVIDER: {provider!r}. "
            f"Expected one of: {', '.join(_MODEL_IDS)}"
        )
    if tier not in ("default", "strong"):
        raise ValueError(f"Unknown tier: {tier!r}. Expected 'default' or 'strong'.")

    model_id = _MODEL_IDS[provider][tier]
    if provider == "google":
        return model_id  # native Gemini string — ADK talks to it directly
    return LiteLlm(model=model_id)

# --- Sample Provider Selection Output ---
# CARTPILOT_MODEL_PROVIDER="google"    -> get_model("default") -> "gemini-3.5-flash"
# CARTPILOT_MODEL_PROVIDER="openai"    -> get_model("default") -> LiteLlm(model="openai/gpt-4o-mini")
# CARTPILOT_MODEL_PROVIDER="anthropic" -> get_model("default") -> LiteLlm(model="anthropic/claude-haiku-4-5")
# CARTPILOT_MODEL_PROVIDER="ollama"    -> get_model("default") -> LiteLlm(model="ollama_chat/llama3.2")

