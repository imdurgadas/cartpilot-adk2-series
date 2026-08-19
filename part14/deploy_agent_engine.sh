#!/usr/bin/env bash
# Part 14 — deploy CartPilot to Google Cloud's managed Agent Runtime
# (the service historically called "Vertex AI Agent Engine" — the CLI
# subcommand still uses that name as of this writing; check
# https://adk.dev/deploy/ for current terminology).
# Fully managed, no container/Dockerfile management required.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID env var}"
REGION="${REGION:-us-central1}"

adk deploy agent_engine \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --display_name="CartPilot" \
  --trace_to_cloud \
  cartpilot
