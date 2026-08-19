"""
Part 12 — CI-style regression gate for CartPilot.

Run with: pytest tests/ -v
This calls the REAL Gemini API for every eval case, so it costs real
tokens and takes real time — that's expected for an eval suite, and is
itself worth tracking with Part 10's cost callback if you run it often.
"""

# Third-party environment variable loader and Pytest test framework
from dotenv import find_dotenv, load_dotenv
import pytest

load_dotenv(find_dotenv())

# Google ADK AgentEvaluator for trajectory and response evaluation
from google.adk.evaluation.agent_evaluator import AgentEvaluator




@pytest.mark.asyncio
async def test_search_agent_basic_trajectory():
    """Regression gate: search_agent must call search_products with
    sensible args and produce a response that matches the reference
    closely enough (ROUGE-based response_match_score), for both a
    successful search and a graceful no-results case."""
    await AgentEvaluator.evaluate(
        agent_module="cartpilot",
        eval_dataset_file_path_or_dir="tests/search.test.json",
    )

# --- Pytest Evaluation Run Output ---
# $ pytest tests/ -v
# ============================= test session starts ==============================
# collected 1 item
#
# tests/test_cartpilot_eval.py::test_search_agent_basic_trajectory PASSED  [100%]
#   - find_water_bottle: tool_trajectory_score=1.0, response_match_score=0.82 (PASS)
#   - no_results_handled_gracefully: tool_trajectory_score=1.0, response_match_score=0.78 (PASS)
# ============================== 1 passed in 3.42s ===============================

