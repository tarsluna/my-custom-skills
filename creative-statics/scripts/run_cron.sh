#!/bin/zsh
# Creative iteration cron wrapper — invoked by launchd every 2 hours.
# Steps: build iteration → heuristic audit → refresh zip on Desktop.

set -euo pipefail

# Provide your fal.ai key via the environment (never hardcode it here).
# e.g. pull from the macOS keychain like the SKILL.md example does:
#   export FAL_KEY="$(security find-generic-password -a "$USER" -s FAL_KEY -w)"
: "${FAL_KEY:?FAL_KEY must be set in the environment}"
export MAX_ITER="${MAX_ITER:-6}"

PIPELINE="${PIPELINE:-$HOME/skills/projects/client-slug/05-meta-ads/pipeline}"
LOG="$PIPELINE/cron.log"

{
  echo ""
  echo "======== $(date +"%Y-%m-%d %H:%M:%S") ========"
  /usr/bin/python3 "$PIPELINE/build_iteration.py" || echo "iteration failed rc=$?"
  /usr/bin/python3 "$PIPELINE/audit_heuristic.py" --latest || echo "audit failed rc=$?"
  /usr/bin/python3 "$PIPELINE/package_delivery.py" --notify || echo "package failed rc=$?"
} >> "$LOG" 2>&1
