#!/bin/bash
set -e

# Визначаємо директорію скрипта та корінь репозиторію
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR" # Переконуємось, що ми в корені репозиторію

# Завантажуємо конфігурацію, якщо є .env
if [ -f ".env" ]; then
  # Читаємо змінні безпечно
  AGE_RECIPIENT=$(grep '^AGE_RECIPIENT=' .env | cut -d'=' -f2 | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//')
else
  echo "[❌] Файл конфігурації .env не знайдено в корені репозиторію ($REPO_DIR)."
  echo "[ℹ️] Будь ласка, створіть .env з .env.example та налаштуйте його."
  exit 1
fi

# Перевірка наявності публічного ключа отримувача
if [ -z "$AGE_RECIPIENT" ]; then
  echo "[❌] Змінна AGE_RECIPIENT не визначена у файлі .env або порожня."
  echo "[ℹ️] Будь ласка, встановіть AGE_RECIPIENT у файлі .env."
  echo "    Його можна отримати з вашого приватного ключа командою: age-keygen -y /шлях/до/вашого/age-key.txt"
  echo "    Або, якщо ключ GPG-зашифрований: gpg -d /шлях/до/ключа.gpg | age-keygen -y -"
  exit 1
fi

echo "[ℹ️] Пошук нешифрованих .md файлів для шифрування (крім README.md)..."
FILES_ENCRYPTED_COUNT=0
FILES_SKIPPED_COUNT=0
FILES_ALREADY_ENCRYPTED_COUNT=0
FILES_FAILED_ENCRYPTION_COUNT=0
FILES_FAILED_SHRED_COUNT=0

# Використовуємо find для кращої обробки імен файлів з пробілами тощо.
# Ігноруємо директорії, якщо вони випадково мають .md розширення.
find . -maxdepth 1 -type f -name "*.md" -print0 | while IFS= read -r -d $'\0' FILE_PATH_RAW; do
  # Обробка шляху, якщо find повертає ./file.md
  FILE_PATH="${FILE_PATH_RAW#./}"
  BASENAME_FILE=$(basename "$FILE_PATH")

  if [[ "$BASENAME_FILE" == "README.md" ]]; then
    echo "[⏭️] Пропускаю $BASENAME_FILE (файл README)"
    ((FILES_SKIPPED_COUNT++))
    continue
  fi

  AGEFILE="$BASENAME_FILE.age" # Шифрований файл буде в корені

  # Перевіряємо, чи існує вже зашифрований файл
  if [[ -f "$AGEFILE" ]]; then
    # Додаткова перевірка: якщо розшифрований файл новіший за зашифрований, його треба перешифрувати
    if [[ "$FILE_PATH" -nt "$AGEFILE" ]]; then
      echo "[⚠️] Файл $BASENAME_FILE новіший за $AGEFILE. Перешифровую."
      # Продовжуємо до блоку шифрування
    else
      echo "[✅] Пропускаю $BASENAME_FILE — відповідний $AGEFILE існує і не старіший."
      ((FILES_ALREADY_ENCRYPTED_COUNT++))
      # Якщо розшифрований файл існує і не новіший за зашифрований,
      # його слід безпечно видалити, щоб не залишати розшифрованих даних.
      # Це особливо важливо, якщо користувач просто запустив encrypt-unencrypted.sh,
      # а не encrypt-n-store.sh, який би і так видалив.
      echo "[🗑️] Розшифрований файл '$BASENAME_FILE' існує поруч із актуальним '$AGEFILE'. Видаляю оригінал..."
      if shred -u "$FILE_PATH"; then
        echo "[✅] Оригінал '$BASENAME_FILE' успішно видалено."
      else
        echo "[❌] Помилка під час видалення '$FILE_PATH' за допомогою shred! Будь ласка, видаліть його вручну та безпечно."
        ((FILES_FAILED_SHRED_COUNT++))
      fi
      continue # Переходимо до наступного файлу
    fi
  fi

  echo "[🔐] Шифрую $BASENAME_FILE → $AGEFILE..."
  if age -r "$AGE_RECIPIENT" -o "$AGEFILE" "$FILE_PATH"; then
    echo "[🗑️] Безпечно видаляю оригінал $BASENAME_FILE..."
    if shred -u "$FILE_PATH"; then
      echo "[✅] Файл $BASENAME_FILE успішно зашифровано та оригінал видалено."
      ((FILES_ENCRYPTED_COUNT++))
    else
      echo "[❌] Помилка під час видалення $FILE_PATH за допомогою shred! Будь ласка, видаліть його вручну та безпечно."
      ((FILES_FAILED_SHRED_COUNT++))
      # Файл зашифровано, але оригінал не видалено - це проблема.
      # Можливо, варто зупинити скрипт тут або додати в окремий список помилок.
    fi
  else
    echo "[❌] Помилка під час шифрування $BASENAME_FILE! Оригінал не видалено."
    ((FILES_FAILED_ENCRYPTION_COUNT++))
  fi
done

echo ""
echo "[📊] Звіт по шифруванню:"
echo "    Зашифровано нових/оновлених файлів: $FILES_ENCRYPTED_COUNT"
echo "    Пропущено (README.md): $FILES_SKIPPED_COUNT"
echo "    Вже були зашифровані (і актуальні): $FILES_ALREADY_ENCRYPTED_COUNT"
if [ $FILES_FAILED_ENCRYPTION_COUNT -gt 0 ]; then
    echo "    [❗] Помилок шифрування: $FILES_FAILED_ENCRYPTION_COUNT"
fi
if [ $FILES_FAILED_SHRED_COUNT -gt 0 ]; then
    echo "    [❗] Помилок безпечного видалення оригіналів: $FILES_FAILED_SHRED_COUNT"
fi

if [ $FILES_FAILED_ENCRYPTION_COUNT -eq 0 ] && [ $FILES_FAILED_SHRED_COUNT -eq 0 ]; then
  echo "[👍] Шифрування незашифрованих .md файлів успішно завершено."
else
  echo "[⚠️] Шифрування завершено з помилками. Будь ласка, перегляньте лог вище."
  exit 1 # Виходимо з помилкою, якщо були проблеми
fi