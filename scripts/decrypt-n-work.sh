#!/bin/bash
set -e

source .env

REPO_DIR="$(dirname "$0")/.."
cd "$REPO_DIR"

FILES=$(ls *.md.age 2>/dev/null | fzf -m --prompt="Вибери файли для розшифрування:")

for FILE in $FILES; do
  OUT="${FILE%.age}"
  age -d -i "$AGE_KEY_FILE" -o "$OUT" "$FILE"
done
