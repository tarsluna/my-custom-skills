#!/usr/bin/env bash
# À lancer avant de publier votre copie : cherche des secrets et les termes privés que vous listez.
# Vos termes : un par ligne dans .leak-terms à la racine (fichier ignoré par git), ou fichier passé en argument.
set -uo pipefail
cd "$(dirname "$0")/.."
terms="${1:-.leak-terms}"
excl=(--exclude-dir=node_modules --exclude-dir=.next --exclude-dir=.git --exclude=package-lock.json --exclude=.leak-terms --exclude=check-leaks.sh)
found=0

scan() {
  local label="$1" pattern="$2" out
  out=$(grep -rIlE "${excl[@]}" -- "$pattern" . 2>/dev/null)
  if [ -n "$out" ]; then
    echo "ALERTE $label :"
    printf '%s\n' "$out" | sed 's/^/  /'
    found=1
  fi
}

scan "cle OpenRouter" 'sk-or-v[0-9]-[a-zA-Z0-9]{10,}'
scan "jeton Apify" 'apify_api_[a-zA-Z0-9]{10,}'
scan "jeton Bearer en dur" 'Bearer [A-Za-z0-9_-]{20,}'
scan "cle privee" 'BEGIN [A-Z ]*PRIVATE KEY'
scan "chemin personnel" '/(Users|home)/[a-z0-9_-]+/'

# Longues chaines en dur : on montre le fichier, jamais la valeur.
long=$(grep -rIlE "${excl[@]}" --include='*.ts' --include='*.tsx' --include='*.json' --include='*.md' --include='*.example' -- "[\"'=][A-Za-z0-9_-]{40,}[\"']?" . 2>/dev/null)
if [ -n "$long" ]; then
  echo "A verifier, longues chaines en dur :"
  printf '%s\n' "$long" | sed 's/^/  /'
fi

if [ -f "$terms" ]; then
  while IFS= read -r term; do
    [ -z "$term" ] && continue
    out=$(grep -rIilE "${excl[@]}" -- "$term" . 2>/dev/null)
    if [ -n "$out" ]; then
      echo "ALERTE terme prive :"
      printf '%s\n' "$out" | sed 's/^/  /'
      found=1
    fi
  done <"$terms"
else
  echo "Aucune liste de termes prives ($terms) : seuls les secrets ont ete cherches."
fi

if [ "$found" -ne 0 ]; then
  echo "Des elements sont a corriger avant publication."
  exit 1
fi
echo "Aucune fuite detectee."
