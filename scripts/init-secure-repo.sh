#!/bin/bash
set -e

NAME="$1"
if [ -z "$NAME" ]; then
  echo "🔧 Використання: ./init-secure-repo.sh <назва>"
  exit 1
fi

mkdir -p "$NAME/scripts" "$NAME/personal-scripts" "$NAME/backup"
cd "$NAME"
git init

# README.md
cat > README.md <<EOF
# $NAME

Цей репозиторій зберігає зашифровані чутливі дані.
EOF

# .gitignore
cat > .gitignore <<EOF
*.md
!README.md
!*.md.age

age-key.txt
backup/
personal-scripts/
EOF

# Базові скрипти
cat > scripts/encrypt-unencrypted.sh <<'EOF'
#!/bin/bash
set -e
KEY_PATH="age-key.txt"
RECIPIENT=$(grep 'public key:' "$KEY_PATH" | awk '{print $3}')
for FILE in *.md; do
  [[ "$FILE" == "README.md" ]] && continue
  [[ -f "$FILE.age" ]] && continue
  echo "[🔐] Шифрую $FILE"
  age -r "$RECIPIENT" -o "$FILE.age" "$FILE"
  shred -u "$FILE"
done
EOF

cat > scripts/encrypt-n-store.sh <<'EOF'
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
fi
EOF

cat > scripts/decrypt-n-work.sh <<'EOF'
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
EOF

cat > scripts/backup-to-cloud.sh <<'EOF'
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
EOF

# Дозволи
chmod +x scripts/*.sh

echo "[✅] Готово! Створено укріплений репозиторій '$NAME'"
