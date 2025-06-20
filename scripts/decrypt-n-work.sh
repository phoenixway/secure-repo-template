#!/bin/bash
set -e

REPO_DIR="$(dirname "$0")/.."
cd "$REPO_DIR"

KEY_PATH="age-key.txt"
FILES=$(ls *.md.age 2>/dev/null | fzf -m --prompt="Вибери файли для розшифрування:")

for FILE in $FILES; do
  OUT="${FILE%.age}"
  age -d -i "$KEY_PATH" -o "$OUT" "$FILE"
done
