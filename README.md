# Agentic Commerce with ADK 2 — Building & Shipping CartPilot

A 14-part blog series building CartPilot, a production-minded multi-agent
shopping & support assistant, with Google's Agent Development Kit (ADK) 2.0
and the Gemini API.

## Contents

- `part01/` … `part18/` — runnable code snapshots for each part of the series.
- `shared/catalog.py` — the mock product catalog reused throughout.

## Series Index

1. Your First ADK 2 Agent: From Zero to `adk web`
2. Giving Agents Tools: Python Functions as First-Class Capabilities
3. Sessions & State: Making CartPilot Remember the Cart
4. Guaranteed Structured Output with Pydantic Schemas
5. From Executor to Graph: ADK 2's Workflow Runtime
6. Multi-Agent by Design: Coordinator and Specialist Sub-Agents
7. The Task API: Structured Agent-to-Agent Delegation
8. Human-in-the-Loop: Pausing for Approval on High-Stakes Actions
9. Resilient Tools: ADK's Error Conventions & Self-Healing Agents
10. Token Economics & Cost Optimization for Agents
11. Guardrails & Observability with Callbacks
12. Evaluating CartPilot: ADK's Eval Framework
13. Extending CartPilot with MCP Tools
14. Shipping CartPilot: Deployment & Production Operations
15. **Bonus** — Bring Your Own Model: Any LLM, Cloud or Local, with ADK 2
16. **Bonus** — Total Cost of Ownership (TCO) & Token Budgeting for Agent Systems
17. **Bonus** — Multi-Provider TCO Comparison: Gemini vs. OpenAI vs. Anthropic vs. Ollama
18. **Bonus** — Self-Hosted Native Production Deployment: Docker Compose, Postgres, Caddy, Jaeger & Loki

## Running any part locally

```bash
cd partNN
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then add your Gemini API key
adk web
```

Get a Gemini API key at https://aistudio.google.com/apikey — no GCP
project or billing setup needed for local development.

## A note on freshness

ADK Python 2.0 reached general availability May 19, 2026 — very recent
at time of writing. A few surfaces referenced in later parts (the Task
API's `mode` parameter, graph-native custom nodes) were still
stabilizing; each relevant post flags this inline and points to
https://adk.dev for the current API if something doesn't match.
