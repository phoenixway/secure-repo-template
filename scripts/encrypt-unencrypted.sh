#!/bin/bash
set -e

source .env

# Перевірка наявності ключа
if [ ! -f "$AGE_KEY_FILE" ]; then
  echo "[❌] Файл $AGE_KEY_FILE не знайдено!"
  exit 1
fi

if [ -z "$AGE_RECIPIENT" ]; then
  echo "[❌] Не вдалося знайти публічний ключ у $AGE_KEY_FILE"
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
  age -r "$AGE_RECIPIENT" -o "$AGEFILE" "$FILE"
  shred -u "$FILE"
done

echo "[✅] Усі нешифровані .md файли зашифровано"
