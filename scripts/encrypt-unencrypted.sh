#!/bin/bash
set -e

KEY_PATH="age-key.txt"

# Перевірка наявності ключа
if [ ! -f "$KEY_PATH" ]; then
  echo "[❌] Файл $KEY_PATH не знайдено!"
  exit 1
fi

# Отримати публічний ключ
RECIPIENT=$(grep 'public key:' "$KEY_PATH" | awk '{print $3}')

if [ -z "$RECIPIENT" ]; then
  echo "[❌] Не вдалося знайти публічний ключ у $KEY_PATH"
  exit 1
fi

# Обійти всі .md файли, крім README.md і тих, що вже зашифровані
for FILE in *.md; do
  if [[ "$FILE" == "README.md" ]]; then
    echo "[ℹ️] Пропускаю $FILE"
    continue
  fi

  AGEFILE="$FILE.age"

  if [[ -f "$AGEFILE" ]]; then
    echo "[ℹ️] Пропускаю $FILE — вже зашифровано"
    continue
  fi

  echo "[🔐] Шифрую $FILE → $AGEFILE"
  age -r "$RECIPIENT" -o "$AGEFILE" "$FILE"
  shred -u "$FILE"
done

echo "[✅] Усі нешифровані .md файли зашифровано"
