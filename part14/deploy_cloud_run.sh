#!/usr/bin/env bash
# Part 14 — deploy CartPilot to Cloud Run.
# Simplest path: let ADK build from source directly (no Dockerfile needed).
# Requires: gcloud auth login && gcloud config set project <PROJECT_ID>
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID env var}"
REGION="${REGION:-us-central1}"

adk deploy cloud_run \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --service_name="cartpilot" \
  --with_ui \
  --trace_to_cloud \
  cartpilot
