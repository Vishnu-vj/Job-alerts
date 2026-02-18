#!/usr/bin/env bash
set -euo pipefail

# If you're using uv:
# uv run job-alerts --config config/sources.yaml --only-enabled

PYTHONPATH=src python3 -m job_alerts.main --config config/sources.yaml --only-enabled

