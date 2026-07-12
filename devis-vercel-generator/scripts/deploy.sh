#!/usr/bin/env bash
# deploy.sh
#
# Deploys a generated devis page to Vercel under the alias pattern
# devis-{client-slug}.vercel.app and returns the final public URL.
#
# Usage:
#   scripts/deploy.sh <output-dir> <client-slug>
#
# Example:
#   scripts/deploy.sh \
#     ~/skills/projects/acme/07-devis-page \
#     acme
#
# Requires:
#   - vercel CLI installed and logged in (vercel login)
#   - The output dir must already contain index.html + vercel.json

set -euo pipefail

OUT_DIR="${1:-}"
CLIENT_SLUG="${2:-}"

if [[ -z "$OUT_DIR" || -z "$CLIENT_SLUG" ]]; then
  echo "Usage: scripts/deploy.sh <output-dir> <client-slug>"
  exit 1
fi

if [[ ! -d "$OUT_DIR" ]]; then
  echo "[!] Output dir not found: $OUT_DIR"
  exit 1
fi

if [[ ! -f "$OUT_DIR/index.html" || ! -f "$OUT_DIR/vercel.json" ]]; then
  echo "[!] $OUT_DIR must contain index.html and vercel.json"
  echo "    Run scripts/generate.mjs first."
  exit 1
fi

PROJECT_NAME="devis-${CLIENT_SLUG}-lf"
EXPECTED_URL="https://${PROJECT_NAME}.vercel.app"

echo "-> Deploying $OUT_DIR as $PROJECT_NAME"
cd "$OUT_DIR"

# Deploy to prod, auto-confirm, named project for stable alias
DEPLOY_OUTPUT="$(vercel --prod --yes --name "$PROJECT_NAME" 2>&1 || true)"

echo "$DEPLOY_OUTPUT"

# Extract the deployment URL (last https://...vercel.app line in output)
DEPLOY_URL="$(echo "$DEPLOY_OUTPUT" | grep -Eo 'https://[a-zA-Z0-9.-]+\.vercel\.app' | tail -n1 || true)"

if [[ -z "$DEPLOY_URL" ]]; then
  echo "[!] Could not extract deployment URL from output above."
  echo "    Check 'vercel ls' manually."
  exit 2
fi

echo ""
echo "=== Deployment done ==="
echo "Deployment URL : $DEPLOY_URL"
echo "Alias URL      : $EXPECTED_URL"
echo ""
echo "Vérifie dans le navigateur :"
echo "  $EXPECTED_URL"
