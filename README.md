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

### 1. Environment Setup

Create a `.env` file in the root directory (or inside the specific `partNN` directory):

```bash
cp part01/.env.example .env
```

Add your Gemini API key inside `.env`:

```env
# Get a key at https://aistudio.google.com/apikey
GOOGLE_API_KEY=your-gemini-api-key-here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

> **Note:** Get a Gemini API key at https://aistudio.google.com/apikey — no GCP project or billing setup needed for local development.

---

### 2. Install & Run

Activate your virtual environment and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r part01/requirements.txt
```

You can run `adk web` either from the root directory pointing to any part, or from within the part directory:

**Option A — From repository root (Recommended):**
```bash
adk web part01
# or part02, part06, etc.
```

**Option B — From inside a part directory:**
```bash
cd part01
adk web
```

---

### 3. Testing the Agent

- **Web UI:** Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Select the agent (e.g. `cartpilot_search`) and start chatting.
- **Terminal CLI:** Alternatively, run an interactive CLI session without a browser:
  ```bash
  adk run part01/cartpilot_search
  ```
- **Test Playbook & Prompt Sequences:** See [instructions.md](instructions.md) for step-by-step test prompt sequences and expected tool outputs for every part (Part 1 through 18).

## A note on freshness

ADK Python 2.0 reached general availability May 19, 2026 — very recent
at time of writing. A few surfaces referenced in later parts (the Task
API's `mode` parameter, graph-native custom nodes) were still
stabilizing; each relevant post flags this inline and points to
https://adk.dev for the current API if something doesn't match.
