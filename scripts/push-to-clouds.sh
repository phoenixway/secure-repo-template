#!/bin/bash
set -e

SCRIPT_DIR="$(dirname "$0")"
REPO_DIR="$SCRIPT_DIR/.."
cd "$REPO_DIR"

BACKUP_DIR="backup"
KEY_PATH="age-key.txt"
DATE=$(date +"%Y-%m-%d-%H%M")
ARCHIVE_NAME="secure-repo-$DATE.tar.gz"
ARCHIVE_PATH="$BACKUP_DIR/$ARCHIVE_NAME"
ENCRYPTED_ARCHIVE="$ARCHIVE_PATH.age"

RECIPIENT=$(grep 'public key:' "$KEY_PATH" | awk '{print $3}')

mkdir -p "$BACKUP_DIR"

echo "[📦] Creating archive of encrypted content..."
tar czf "$ARCHIVE_PATH" *.md.age README.md .git

echo "[🔐] Encrypting archive with age..."
age -r "$RECIPIENT" -o "$ENCRYPTED_ARCHIVE" "$ARCHIVE_PATH"

shred -u "$ARCHIVE_PATH"

# Multiple remotes (configure in rclone first)
REMOTES=("cloud1:" "cloud2:" "cloud3:")

for remote in "${REMOTES[@]}"; do
  echo "[☁️] Uploading to $remote..."
  rclone copy "$ENCRYPTED_ARCHIVE" "$remote"
done

echo "[✅] Encrypted backup pushed to all clouds."
