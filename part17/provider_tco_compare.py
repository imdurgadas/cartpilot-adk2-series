"""
Part 17 (bonus) — extending Part 16's TCO calculator across every
provider Part 15 wired up (Gemini, OpenAI, Anthropic, local Ollama),
so "which provider is actually cheaper for CartPilot" is an answer you
compute, not a guess based on a single provider's list price.

Only the LLM pricing table changes per provider. Every other cost
center from Part 16 — hosting, third-party MCP tools, eval/CI runs,
human-in-the-loop review time, observability storage — is assumed
constant, because none of them are determined by which model answers
CartPilot's questions. That assumption is itself worth stating plainly:
if a weaker model means MORE human review (Part 8) because it makes
more mistakes needing correction, that's a real cost this script does
NOT model automatically — see the caveats at the bottom of this file
and the accompanying blog post.

Run: python provider_tco_compare.py
"""

from dataclasses import dataclass, field

# --- Illustrative per-million-token pricing, one entry per provider/tier. ---
# ALWAYS verify current pricing before using this for real budgeting:
#   Google:    https://ai.google.dev/gemini-api/docs/pricing
#   OpenAI:    https://openai.com/api/pricing
#   Anthropic: https://www.anthropic.com/pricing
#   Ollama:    no per-token cost — see LOCAL_HARDWARE_MONTHLY_USD below.
PROVIDER_PRICING = {
    "google": {
        "default": {"input": 0.30, "output": 2.50},   # gemini-3.5-flash
        "strong":  {"input": 1.25, "output": 10.00},  # gemini-2.5-pro
    },
    "openai": {
        "default": {"input": 0.15, "output": 0.60},   # gpt-4o-mini
        "strong":  {"input": 2.50, "output": 10.00},  # gpt-4o
    },
    "anthropic": {
        "default": {"input": 0.80, "output": 4.00},   # claude-haiku-4-5
        "strong":  {"input": 3.00, "output": 15.00},  # claude-sonnet-4-5
    },
    "ollama": {
        "default": {"input": 0.0, "output": 0.0},     # local — no per-token cost
        "strong":  {"input": 0.0, "output": 0.0},
    },
}

# A fully local Ollama setup isn't free — it's a different cost SHAPE:
# a fixed monthly hardware/power cost instead of a per-token one.
# Set this to $0 if you're running on hardware you already own and
# would be paying for regardless of CartPilot; set it to a real
# amortized GPU server cost if this deployment is the reason you
# bought or rented that hardware.
LOCAL_HARDWARE_MONTHLY_USD = 400.0  # e.g. an amortized on-prem GPU box


@dataclass
class AgentProfile:
    """Provider-independent usage shape for one agent — how OFTEN and
    how MUCH it talks has nothing to do with which provider answers."""
    name: str
    tier: str  # "default" or "strong" — looked up per-provider at compute time
    calls_per_conversation: float
    avg_input_tokens_per_call: int
    avg_output_tokens_per_call: int

    def cost_per_conversation(self, provider: str) -> float:
        prices = PROVIDER_PRICING[provider][self.tier]
        input_cost = (self.avg_input_tokens_per_call * self.calls_per_conversation
                       / 1_000_000 * prices["input"])
        output_cost = (self.avg_output_tokens_per_call * self.calls_per_conversation
                        / 1_000_000 * prices["output"])
        return input_cost + output_cost


@dataclass
class FixedCosts:
    """Everything from Part 16 that does NOT vary by model provider."""
    hosting_monthly_usd: float = 150.0
    mcp_calls_per_conversation: float = 0.3
    mcp_cost_per_call_usd: float = 0.01
    deploys_per_month: int = 20
    eval_cases: int = 25
    avg_eval_cost_per_case_usd: float = 0.002
    refunds_needing_approval_per_month: int = 40
    avg_approval_review_minutes: float = 3.0
    reviewer_hourly_rate_usd: float = 35.0
    log_events_per_conversation: float = 12.0
    log_storage_cost_per_million_events_usd: float = 5.0


def compute_tco_for_provider(provider: str, conversations_per_month: int,
                              agents: list[AgentProfile], fixed: FixedCosts) -> dict:
    llm_cost_monthly = sum(a.cost_per_conversation(provider) for a in agents) * conversations_per_month

    mcp_cost_monthly = fixed.mcp_calls_per_conversation * conversations_per_month * fixed.mcp_cost_per_call_usd
    eval_cost_monthly = fixed.deploys_per_month * fixed.eval_cases * fixed.avg_eval_cost_per_case_usd
    hitl_hours = fixed.refunds_needing_approval_per_month * fixed.avg_approval_review_minutes / 60
    hitl_cost_monthly = hitl_hours * fixed.reviewer_hourly_rate_usd
    log_cost_monthly = (fixed.log_events_per_conversation * conversations_per_month
                         / 1_000_000 * fixed.log_storage_cost_per_million_events_usd)

    hosting_cost = fixed.hosting_monthly_usd
    if provider == "ollama":
        # Swap the cloud LLM API line for a local hardware line — the
        # "hosting" cost for a local-model deployment includes running
        # the model, not just the ADK app container.
        hosting_cost += LOCAL_HARDWARE_MONTHLY_USD

    total = llm_cost_monthly + hosting_cost + mcp_cost_monthly + eval_cost_monthly + hitl_cost_monthly + log_cost_monthly

    return {
        "provider": provider,
        "llm_api_cost": round(llm_cost_monthly, 2),
        "hosting_cost": round(hosting_cost, 2),
        "mcp_tool_cost": round(mcp_cost_monthly, 2),
        "eval_ci_cost": round(eval_cost_monthly, 2),
        "human_review_cost": round(hitl_cost_monthly, 2),
        "observability_cost": round(log_cost_monthly, 2),
        "total_monthly_usd": round(total, 2),
        "cost_per_conversation_usd": round(total / conversations_per_month, 4),
    }


def print_comparison(results: list[dict]) -> None:
    print(f"{'Provider':<12} {'LLM API':>12} {'Hosting':>12} {'Total/mo':>12} {'Per convo':>12}")
    print("-" * 62)
    for r in results:
        print(f"{r['provider']:<12} ${r['llm_api_cost']:>10,.2f} ${r['hosting_cost']:>10,.2f} "
              f"${r['total_monthly_usd']:>10,.2f} ${r['cost_per_conversation_usd']:>10,.4f}")


if __name__ == "__main__":
    # Same CartPilot shape used throughout this series: coordinator +
    # three specialists, support_agent on the "strong" tier everywhere
    # (mirrors Part 10's tiering decision, now priced per-provider).
    conversations_per_month = 50_000
    agents = [
        AgentProfile("coordinator", "default", calls_per_conversation=3.0,
                      avg_input_tokens_per_call=900, avg_output_tokens_per_call=60),
        AgentProfile("search_agent", "default", calls_per_conversation=1.4,
                      avg_input_tokens_per_call=1100, avg_output_tokens_per_call=120),
        AgentProfile("cart_agent", "default", calls_per_conversation=1.1,
                      avg_input_tokens_per_call=1400, avg_output_tokens_per_call=180),
        AgentProfile("support_agent", "strong", calls_per_conversation=0.6,
                      avg_input_tokens_per_call=1600, avg_output_tokens_per_call=220),
    ]
    fixed = FixedCosts()

    results = [compute_tco_for_provider(p, conversations_per_month, agents, fixed)
               for p in PROVIDER_PRICING]

    print(f"=== CartPilot Monthly TCO by Provider ({conversations_per_month:,} conversations/mo) ===\n")
    print_comparison(results)
    print(
        "\nCaveats — read before acting on this table:\n"
        "  1. Pricing is illustrative and WILL drift — verify current rates.\n"
        "  2. This assumes every provider produces equally acceptable output.\n"
        "     Only compare providers that clear the SAME bar on Part 12's eval\n"
        "     suite — a cheaper provider that needs more human correction\n"
        "     (Part 8) is not actually cheaper once you account for that.\n"
        "  3. Ollama's hosting line is a rough hardware amortization guess —\n"
        "     replace LOCAL_HARDWARE_MONTHLY_USD with your real number.\n"
        "  4. Latency and rate limits differ by provider and aren't priced\n"
        "     here at all, but affect user experience and support load."
    )

# --- Sample Comparison Run Output ---
# $ python provider_tco_compare.py
# === CartPilot Monthly TCO by Provider (50,000 conversations/mo) ===
#
# Provider          LLM API      Hosting     Total/mo    Per convo
# --------------------------------------------------------------
# google       $    280.95 $    150.00 $    654.95 $    0.0131
# openai       $    245.73 $    150.00 $    619.73 $    0.0124
# anthropic    $    583.40 $    150.00 $    957.40 $    0.0191
# ollama       $      0.00 $    550.00 $    774.00 $    0.0155
#
# Caveats — read before acting on this table:
#   1. Pricing is illustrative and WILL drift — verify current rates.
#   2. This assumes every provider produces equally acceptable output.
#      Only compare providers that clear the SAME bar on Part 12's eval
#      suite — a cheaper provider that needs more human correction
#      (Part 8) is not actually cheaper once you account for that.
#   3. Ollama's hosting line is a rough hardware amortization guess —
#      replace LOCAL_HARDWARE_MONTHLY_USD with your real number.
#   4. Latency and rate limits differ by provider and aren't priced
#      here at all, but affect user experience and support load.

