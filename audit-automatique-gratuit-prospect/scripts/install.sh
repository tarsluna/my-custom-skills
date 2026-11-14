#!/usr/bin/env bash
# Installe les dépendances, crée les .env manquants et vérifie que tout compile. Ne dépense aucun crédit.
set -euo pipefail
cd "$(dirname "$0")/../template"

major=$(node -p 'process.versions.node.split(".")[0]')
if [ "$major" -lt 22 ]; then
  echo "Node 22 ou plus est requis (version trouvée : $major)." >&2
  exit 1
fi

for app in backend frontend; do
  echo "== $app : dépendances"
  (cd "$app" && npm ci)
  [ -f "$app/.env" ] || cp "$app/.env.example" "$app/.env"
  echo "== $app : types"
  (cd "$app" && npx tsc --noEmit)
done

echo "== backend : tests"
(cd backend && npm test)

cat <<'FIN'

Installation terminée.
1. Adaptez template/backend/audit.config.json à votre métier.
2. Démonstration sans clé : cd template/frontend && USE_FIXTURES=1 npm run dev
3. Suivez references/07-plan-de-test.md avant de dépenser des crédits.
FIN
