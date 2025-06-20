#!/bin/bash
set -e

SCRIPT_DIR="$(dirname "$0")"
REPO_DIR="$SCRIPT_DIR/.."
cd "$REPO_DIR"

KEY_PATH="age-key.txt"
BACKUP_DIR="backup"
DATE=$(date +"%Y-%m-%d-%H%M")
BACKUP_FILE="$BACKUP_DIR/secure-repo-$DATE.tar.gz.age"
RECIPIENT=$(grep 'public key:' "$KEY_PATH" | awk '{print $3}')

mkdir -p "$BACKUP_DIR"

tar czf - *.md.age README.md .git | age -r "$RECIPIENT" -o "$BACKUP_FILE"

rclone copy "$BACKUP_FILE" my-remote:secure-repo-backups/
