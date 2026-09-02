#!/usr/bin/env bash
# Installe tous les skills de ce repo dans ~/.claude/skills (Claude Code).
#
# Usage :
#   bash install.sh            # symlinks (les `git pull` mettent à jour les skills)
#   bash install.sh --copy     # copies indépendantes
#   bash install.sh --check    # liste ce qui est installé / manquant, ne change rien
#   bash install.sh --uninstall
#
# One-liner (sans cloner d'abord) :
#   curl -fsSL https://raw.githubusercontent.com/tarsluna/my-custom-skills/main/install.sh | bash
set -euo pipefail

REPO_URL="https://github.com/tarsluna/my-custom-skills.git"
CLONE_DIR="${MY_SKILLS_DIR:-$HOME/.claude/my-custom-skills}"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
MODE="link"
for arg in "$@"; do
  case "$arg" in
    --copy) MODE="copy" ;;
    --check) MODE="check" ;;
    --uninstall) MODE="uninstall" ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "option inconnue : $arg" >&2; exit 2 ;;
  esac
done

# 1. Localiser le repo : soit on est dedans, soit on le clone/met à jour.
SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-.}")" 2>/dev/null && pwd || true)"
if [ -z "$SRC" ] || [ ! -f "$SRC/install.sh" ] || [ ! -d "$SRC/.git" ]; then
  if [ -d "$CLONE_DIR/.git" ]; then
    echo "→ mise à jour de $CLONE_DIR"; git -C "$CLONE_DIR" pull --ff-only -q
  else
    echo "→ clone dans $CLONE_DIR"; git clone -q "$REPO_URL" "$CLONE_DIR"
  fi
  SRC="$CLONE_DIR"
fi

mkdir -p "$SKILLS_DIR"
installed=0; skipped=0; missing=0
for dir in "$SRC"/*/; do
  name="$(basename "$dir")"
  [ -f "$dir/SKILL.md" ] || continue
  target="$SKILLS_DIR/$name"
  case "$MODE" in
    check)
      if [ -e "$target" ]; then echo "  ✓ $name"; installed=$((installed+1)); else echo "  ✗ $name (absent)"; missing=$((missing+1)); fi ;;
    uninstall)
      if [ -L "$target" ] && [ "$(readlink "$target")" = "${dir%/}" ]; then rm "$target"; echo "  − $name"; installed=$((installed+1)); fi ;;
    link)
      if [ -L "$target" ]; then ln -sfn "${dir%/}" "$target"; installed=$((installed+1))
      elif [ -e "$target" ]; then echo "  ! $name existe déjà (dossier réel) — non touché"; skipped=$((skipped+1))
      else ln -s "${dir%/}" "$target"; echo "  + $name"; installed=$((installed+1)); fi ;;
    copy)
      if [ -e "$target" ] && [ ! -L "$target" ]; then echo "  ! $name existe déjà — non touché"; skipped=$((skipped+1))
      else rm -f "$target"; cp -R "${dir%/}" "$target"; echo "  + $name (copie)"; installed=$((installed+1)); fi ;;
  esac
done
case "$MODE" in
  check) echo "$installed installés, $missing manquants dans $SKILLS_DIR" ;;
  uninstall) echo "$installed liens retirés" ;;
  *) echo "$installed skills installés ($MODE), $skipped ignorés → $SKILLS_DIR"; echo "Relance Claude Code pour les charger." ;;
esac
