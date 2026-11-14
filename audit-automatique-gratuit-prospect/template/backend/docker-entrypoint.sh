#!/bin/sh
# Le volume Railway est monté en root : on lui donne le bon propriétaire, puis on abandonne root.
set -e
if [ "$(id -u)" = "0" ]; then
  dir="${DATA_DIR:-/data}"
  if [ "$(stat -c %U "$dir" 2>/dev/null)" != "node" ]; then chown -R node:node "$dir" 2>/dev/null || true; fi
  exec gosu node "$@"
fi
exec "$@"
