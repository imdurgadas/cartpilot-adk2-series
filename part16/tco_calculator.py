"""
Part 16 (bonus) — Total Cost of Ownership calculator for an ADK agent
system, modeled on CartPilot's own architecture from this series.

Pure stdlib, no external dependencies, no API calls — this is a
planning tool, not a metering tool. Feed it your own assumptions (or
real numbers pulled from Part 10's usage_log once you have production
traffic) and it breaks down where the money actually goes across every
cost center this series introduced, not just raw LLM tokens:

    - LLM API cost           (Part 10)
    - Compute / hosting      (Part 14)
    - Third-party MCP tools  (Part 13)
    - Eval / CI runs         (Part 12)
    - Human-in-the-loop time (Part 8)
    - Observability storage  (Part 11)

Run: python tco_calculator.py
"""

from dataclasses import dataclass, field


@dataclass
class AgentUsage:
    """Per-agent assumptions for one month of CartPilot traffic."""
    name: str
    calls_per_conversation: float          # avg times this agent is invoked per conversation
    avg_input_tokens_per_call: int         # includes instruction + tool schemas + history
    avg_output_tokens_per_call: int
    price_per_million_input: float         # $ — illustrative, use current provider pricing
    price_per_million_output: float

    def cost_per_conversation(self) -> float:
        input_cost = (self.avg_input_tokens_per_call * self.calls_per_conversation
                       / 1_000_000 * self.price_per_million_input)
        output_cost = (self.avg_output_tokens_per_call * self.calls_per_conversation
                        / 1_000_000 * self.price_per_million_output)
        return input_cost + output_cost


@dataclass
class TCOAssumptions:
    conversations_per_month: int
    agents: list[AgentUsage]

    # Part 14 — compute / hosting (Cloud Run / Agent Runtime)
    hosting_monthly_usd: float = 150.0

    # Part 13 — third-party MCP tool costs (e.g. a shipping-rate provider's API fees)
    mcp_calls_per_conversation: float = 0.3
    mcp_cost_per_call_usd: float = 0.01

    # Part 12 — eval suite run in CI on every deploy
    deploys_per_month: int = 20
    eval_cases: int = 25
    avg_eval_cost_per_case_usd: float = 0.002  # tokens spent per eval case, converted to $

    # Part 8 — human-in-the-loop refund approvals
    refunds_needing_approval_per_month: int = 40
    avg_approval_review_minutes: float = 3.0
    reviewer_hourly_rate_usd: float = 35.0

    # Part 11 — structured audit logging / observability storage
    log_events_per_conversation: float = 12.0
    log_storage_cost_per_million_events_usd: float = 5.0


def compute_tco(a: TCOAssumptions) -> dict:
    llm_cost_per_conversation = sum(agent.cost_per_conversation() for agent in a.agents)
    llm_cost_monthly = llm_cost_per_conversation * a.conversations_per_month

    mcp_cost_monthly = (a.mcp_calls_per_conversation * a.conversations_per_month
                         * a.mcp_cost_per_call_usd)

    eval_cost_monthly = a.deploys_per_month * a.eval_cases * a.avg_eval_cost_per_case_usd

    hitl_hours = a.refunds_needing_approval_per_month * a.avg_approval_review_minutes / 60
    hitl_cost_monthly = hitl_hours * a.reviewer_hourly_rate_usd

    log_events_monthly = a.log_events_per_conversation * a.conversations_per_month
    log_cost_monthly = log_events_monthly / 1_000_000 * a.log_storage_cost_per_million_events_usd

    total = (llm_cost_monthly + a.hosting_monthly_usd + mcp_cost_monthly
             + eval_cost_monthly + hitl_cost_monthly + log_cost_monthly)

    return {
        "by_agent": {agent.name: round(agent.cost_per_conversation() * a.conversations_per_month, 2)
                     for agent in a.agents},
        "llm_api_cost": round(llm_cost_monthly, 2),
        "hosting_cost": round(a.hosting_monthly_usd, 2),
        "mcp_tool_cost": round(mcp_cost_monthly, 2),
        "eval_ci_cost": round(eval_cost_monthly, 2),
        "human_review_cost": round(hitl_cost_monthly, 2),
        "observability_cost": round(log_cost_monthly, 2),
        "total_monthly_usd": round(total, 2),
        "cost_per_conversation_usd": round(total / a.conversations_per_month, 4),
    }


def print_report(result: dict) -> None:
    print("=== CartPilot Monthly TCO ===\n")
    print("LLM cost by agent:")
    for name, cost in result["by_agent"].items():
        print(f"  {name:<20} ${cost:>10,.2f}")
    print()
    print(f"{'LLM API (total)':<24} ${result['llm_api_cost']:>10,.2f}")
    print(f"{'Hosting / compute':<24} ${result['hosting_cost']:>10,.2f}")
    print(f"{'Third-party MCP tools':<24} ${result['mcp_tool_cost']:>10,.2f}")
    print(f"{'Eval suite / CI':<24} ${result['eval_ci_cost']:>10,.2f}")
    print(f"{'Human-in-the-loop time':<24} ${result['human_review_cost']:>10,.2f}")
    print(f"{'Observability storage':<24} ${result['observability_cost']:>10,.2f}")
    print("-" * 38)
    print(f"{'TOTAL / month':<24} ${result['total_monthly_usd']:>10,.2f}")
    print(f"{'Cost per conversation':<24} ${result['cost_per_conversation_usd']:>10,.4f}")


if __name__ == "__main__":
    # Illustrative starting point modeled on CartPilot's Parts 6-8 agents.
    # Replace calls_per_conversation and token counts with real numbers
    # pulled from Part 10's usage_log once you have production traffic —
    # this is a planning estimate, not a substitute for measurement.
    assumptions = TCOAssumptions(
        conversations_per_month=50_000,
        agents=[
            AgentUsage("coordinator", calls_per_conversation=3.0,
                       avg_input_tokens_per_call=900, avg_output_tokens_per_call=60,
                       price_per_million_input=0.30, price_per_million_output=2.50),
            AgentUsage("search_agent", calls_per_conversation=1.4,
                       avg_input_tokens_per_call=1100, avg_output_tokens_per_call=120,
                       price_per_million_input=0.30, price_per_million_output=2.50),
            AgentUsage("cart_agent", calls_per_conversation=1.1,
                       avg_input_tokens_per_call=1400, avg_output_tokens_per_call=180,
                       price_per_million_input=0.30, price_per_million_output=2.50),
            AgentUsage("support_agent", calls_per_conversation=0.6,
                       avg_input_tokens_per_call=1600, avg_output_tokens_per_call=220,
                       price_per_million_input=1.25, price_per_million_output=10.00),  # on Pro tier
        ],
    )

    print_report(compute_tco(assumptions))

# --- Sample Run Output ---
# $ python tco_calculator.py
# === CartPilot Monthly TCO ===
#
# LLM cost by agent:
#   coordinator          $     63.00
#   search_agent         $     44.10
#   cart_agent           $     47.85
#   support_agent        $    126.00
#
# LLM API (total)          $    280.95
# Hosting / compute        $    150.00
# Third-party MCP tools    $    150.00
# Eval suite / CI          $      1.00
# Human-in-the-loop time   $     70.00
# Observability storage    $      3.00
# --------------------------------------
# TOTAL / month            $    654.95
# Cost per conversation    $    0.0131
