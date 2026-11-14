#!/usr/bin/env bash
# Contrôle un backend déployé. Sans --launch, ne dépense rien.
#   ADMIN_API_KEY=... scripts/smoke-test.sh https://api.exemple.fr
#   ADMIN_API_KEY=... scripts/smoke-test.sh https://api.exemple.fr --launch exemple.fr   (environ 120 crédits)
set -uo pipefail

API="${1:?Usage : smoke-test.sh <url du backend> [--launch domaine]}"
API="${API%/}"
: "${ADMIN_API_KEY:?Définissez ADMIN_API_KEY dans l environnement}"
fails=0

check() {
  local label="$1" expected="$2" got="$3"
  if [ "$expected" = "$got" ]; then echo "ok    $label"; else echo "ECHEC $label : attendu $expected, obtenu $got"; fails=$((fails + 1)); fi
}
code() { curl -s -m 30 -o /dev/null -w '%{http_code}' "$@"; }

check "sante" 200 "$(code "$API/health")"
check "configuration publique" 200 "$(code "$API/public/config")"
check "admin sans cle refusee" 401 "$(code "$API/admin/stats")"
check "admin avec cle" 200 "$(code -H "x-admin-key: $ADMIN_API_KEY" "$API/admin/stats")"
check "jeton inconnu" 404 "$(code "$API/public/audits/inconnu-AAAAAAAAAAAAAAAAAAAAAA")"
check "webhook sans secret" 401 "$(code -X POST -H 'content-type: application/json' -d '{}' "$API/webhooks/booking")"
robots=$(curl -s -m 30 -D - -o /dev/null "$API/public/config" | tr -d '\r' | awk -F': ' 'tolower($1)=="x-robots-tag"{print $2}')
case "$robots" in *noindex*) echo "ok    noindex" ;; *) echo "ECHEC noindex absent"; fails=$((fails + 1)) ;; esac

if [ "${2:-}" = "--launch" ]; then
  domain="${3:?Indiquez un domaine dont vous avez l accord}"
  echo "Lancement de l audit de $domain (environ 120 credits, 5 a 6 minutes)"
  id=$(curl -s -m 30 -X POST -H "x-admin-key: $ADMIN_API_KEY" -H 'content-type: application/json' -d "{\"domain\":\"$domain\"}" "$API/admin/audits" | python3 -c 'import sys,json;print(json.load(sys.stdin)["auditId"])')
  status=""
  for _ in $(seq 1 80); do
    status=$(curl -s -m 30 -H "x-admin-key: $ADMIN_API_KEY" "$API/admin/audits/$id" | python3 -c 'import sys,json;print(json.load(sys.stdin)["audit"]["status"])')
    case "$status" in ready | failed | needs_domain) break ;; esac
    sleep 15
  done
  check "statut final" ready "$status"

  detail=$(curl -s -m 30 -H "x-admin-key: $ADMIN_API_KEY" "$API/admin/audits/$id")
  token=$(printf '%s' "$detail" | python3 -c 'import sys,json;print(json.load(sys.stdin)["audit"]["token"])')
  check "dix creatives" 10 "$(printf '%s' "$detail" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)["creatives"]))')"

  public=$(curl -s -m 30 "$API/public/audits/$token")
  check "textes verrouilles masques" 0 "$(printf '%s' "$public" | python3 -c 'import sys,json;print(sum(1 for c in json.load(sys.stdin)["creatives"] if c["locked"] and (c["headline"] or c["primaryText"] or c["bullets"])))')"

  for f in $(printf '%s' "$detail" | python3 -c '
import sys,json
for c in json.load(sys.stdin)["creatives"]:
    if c["locked"]:
        print(c["original_file"]); print(c["display_file"]); print(c["thumb_file"])'); do
    check "fichier net inaccessible" 404 "$(code "$API/media/$token/$f")"
  done
  echo "Page : $(printf '%s' "$public" | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])') (a ouvrir sur le front, en /c/<jeton>)"
fi

if [ "$fails" -gt 0 ]; then
  echo "$fails controle(s) en echec."
  exit 1
fi
echo "Tous les controles sont bons."
