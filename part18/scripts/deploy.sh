#!/usr/bin/env bash
# Part 18 — the entire "CI/CD pipeline" for a native deployment: pull,
# run Part 12's eval suite as a pre-deploy gate, rebuild, restart.
# Trigger this by hand over SSH, from a cron job, or from a self-hosted
# CI runner (Gitea Actions, Woodpecker, Jenkins) — none of which is a
# proprietary cloud dependency, unlike a managed CI SaaS.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Pulling latest code"
git pull --ff-only

echo "==> Running eval suite (Part 12) as a pre-deploy gate"
if [ -d tests ]; then
  python -m pytest tests/ -v
else
  echo "(no tests/ directory in this snapshot — skipping)"
fi

echo "==> Building and restarting the stack"
docker compose build cartpilot
docker compose up -d --no-deps cartpilot

echo "==> Deploy complete. Tailing logs (Ctrl+C to stop watching):"
docker compose logs -f --tail=50 cartpilot
