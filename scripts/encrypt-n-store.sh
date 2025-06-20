#!/bin/bash
set -e

# Шлях до папки скриптів
SCRIPT_DIR="./scripts"

# 1. Шифруємо нові або змінені файли
echo "[🔐] Шифрування нешифрованих файлів..."
bash "$SCRIPT_DIR/encrypt-unencrypted.sh"

# 2. Перевірка: чи є зміни в git
if [[ -n $(git status --porcelain) ]]; then
    echo "[📦] Є зміни, додаю у git..."
    git add *.md.age
    git commit -m "Encrypted & committed on $(date '+%Y-%m-%d %H:%M:%S')"
else
    echo "[✔] Немає нових змін — все в актуальному стані"
fi

# 3. (Опційно) пуш у віддалений репозиторій
if git remote | grep -q origin; then
    echo "[☁️] Пушу у віддалений репозиторій..."
    git push origin main
else
    echo "[ℹ️] Віддалений репозиторій не налаштований. Пропускаю push"
fi

echo "[✅] Зберігання завершено"
