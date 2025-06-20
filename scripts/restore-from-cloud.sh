#!/bin/bash
set -e

SCRIPT_DIR="$(dirname "$0")"
REPO_DIR="$SCRIPT_DIR/.."
cd "$REPO_DIR"

source .env

TMP_DIR="tmp-restore"
mkdir -p "$TMP_DIR"

echo "[☁️] Fetching list of backups from cloud..."
REMOTE_LIST=($CLOUD_REMOTES)

select remote in "${REMOTE_LIST[@]}"; do
  [ -n "$remote" ] && break
done

echo "[🔍] Getting file list..."
FILES=$(rclone ls "$remote" | grep ".tar.gz.age" | awk '{print $2}')

if [ -z "$FILES" ]; then
  echo "❌ No backups found on $remote"
  exit 1
fi

echo "Available backups:"
echo "$FILES" | nl

read -p "Enter number of backup to restore: " N
SELECTED=$(echo "$FILES" | sed -n "${N}p")

if [ -z "$SELECTED" ]; then
  echo "Invalid selection"
  exit 1
fi

echo "[⬇️] Downloading $SELECTED..."
rclone copy "$remote/$SELECTED" "$TMP_DIR"

FILEPATH="$TMP_DIR/$(basename "$SELECTED")"
OUTPATH="$TMP_DIR/decrypted.tar.gz"

echo "[🔐] Decrypting archive..."
age -d -i age-key.txt -o "$OUTPATH" "$FILEPATH"

mkdir -p "$TMP_DIR/extracted"
tar xzf "$OUTPATH" -C "$TMP_DIR/extracted"

echo "[✅] Restored content extracted to: $TMP_DIR/extracted/"
