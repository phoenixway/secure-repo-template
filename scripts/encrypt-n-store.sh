#!/bin/bash
set -e

source .env

SCRIPT_DIR="$(dirname "$0")"
REPO_DIR="$SCRIPT_DIR/.."
cd "$REPO_DIR"

bash "$SCRIPT_DIR/encrypt-unencrypted.sh"

if [[ -n $(git status --porcelain) ]]; then
  echo "[📦] Git: committing encrypted files..."
  git add *.md.age
  git commit -m "Encrypted update $(date '+%Y-%m-%d %H:%M:%S')"
fi

if git remote | grep -q origin; then
  echo "[🚀] Git: pushing to origin..."
  git push origin main
else
  echo "[ℹ️] No git remote configured. Skipping git push."
fi

# Cloud backup
echo "[☁️] Starting cloud backup..."
bash "$SCRIPT_DIR/push-to-clouds.sh"
