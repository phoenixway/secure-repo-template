#!/bin/bash
set -e

SCRIPT_DIR="$(dirname "$0")"

bash "$SCRIPT_DIR/encrypt-unencrypted.sh"

cd "$SCRIPT_DIR/.."

if [[ -n $(git status --porcelain) ]]; then
  git add *.md.age
  git commit -m "Encrypted update $(date '+%Y-%m-%d %H:%M:%S')"
fi

if git remote | grep -q origin; then
  git push origin main
else
  echo "[ℹ️] Віддалений репозиторій не налаштований"
fi
