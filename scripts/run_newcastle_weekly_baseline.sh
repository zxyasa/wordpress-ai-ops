#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHONPATH=src python3 -m wp_ai_ops.cli plan-weekly \
  --gsc-csv examples/csv/newcastle_baseline_gsc.csv \
  --ga-csv examples/csv/newcastle_baseline_ga.csv \
  --base-url https://newcastlehub.info \
  --mode plan \
  --top-n 5 \
  --out-dir weekly-output-newcastle-baseline \
  --state-dir .wp-ai-ops-state-live

echo "Generated: weekly-output-newcastle-baseline/tasks + weekly report"
