#!/bin/zsh
# Morning delivery — invoked by launchd at 8:00 local time tomorrow.
# Re-packages everything + tries Mail.app email if configured.

set -euo pipefail

PIPELINE="${PIPELINE:-$HOME/skills/projects/client-slug/05-meta-ads/pipeline}"
LOG="$PIPELINE/delivery.log"

{
  echo ""
  echo "======== MORNING DELIVERY $(date +"%Y-%m-%d %H:%M:%S") ========"
  /usr/bin/python3 "$PIPELINE/package_delivery.py" --email --notify || echo "delivery failed rc=$?"
} >> "$LOG" 2>&1
