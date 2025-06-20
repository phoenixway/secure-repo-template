#!/bin/bash
set -e

# Визначаємо директорію скрипта та корінь репозиторію
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Функції для роботи з ключем ---
# (Вставляємо сюди повний код функцій get_decrypted_age_key та cleanup_temp_key)
# Function to get the path to the decrypted age private key
# It handles GPG decryption to a temporary file if needed.
# Sets DECRYPTED_AGE_KEY_PATH global variable.
# Returns 0 on success, 1 on failure.
# Creates TEMP_KEY_FILE_PATH global variable for cleanup.
get_decrypted_age_key() {
  local master_key_path="$1" # Path from MASTER_AGE_KEY_STORAGE_PATH
  DECRYPTED_AGE_KEY_PATH="" # Reset
  TEMP_KEY_FILE_PATH=""     # Reset

  if [ -z "$master_key_path" ]; then
    echo "[❌] get_decrypted_age_key: Шлях до основного ключа не надано."
    return 1
  fi

  # Якщо master_key_path відносний, робимо його абсолютним відносно REPO_DIR
  if [[ "$master_key_path" != /* ]]; then
    master_key_path="$REPO_DIR/$master_key_path"
  fi

  if [ ! -f "$master_key_path" ]; then
    echo "[❌] get_decrypted_age_key: Файл основного ключа '$master_key_path' не знайдено."
    return 1
  fi

  # Check if the key is GPG encrypted
  if [[ "$master_key_path" == *.gpg ]]; then
    if ! command -v gpg &> /dev/null; then
      echo "[❌] get_decrypted_age_key: Ключ '$master_key_path' зашифровано GPG, але команда 'gpg' не знайдена."
      return 1
    fi
    TEMP_KEY_FILE_PATH="$REPO_DIR/temp_age_key.$RANDOM.$RANDOM.txt"
    echo "[ℹ️] Ключ '$master_key_path' зашифровано GPG. Спроба розшифрування..."
    echo "    Введіть парольну фразу для GPG, щоб розшифрувати '$master_key_path'."
    if gpg --quiet --batch --yes --decrypt -o "$TEMP_KEY_FILE_PATH" "$master_key_path"; then
      DECRYPTED_AGE_KEY_PATH="$TEMP_KEY_FILE_PATH"
      chmod 600 "$DECRYPTED_AGE_KEY_PATH" # Set strict permissions
      echo "[✅] Ключ тимчасово розшифровано в '$DECRYPTED_AGE_KEY_PATH'."
      return 0
    else
      echo "[❌] get_decrypted_age_key: Помилка розшифрування '$master_key_path' за допомогою GPG."
      [ -f "$TEMP_KEY_FILE_PATH" ] && rm -f "$TEMP_KEY_FILE_PATH"
      TEMP_KEY_FILE_PATH=""
      return 1
    fi
  else
    DECRYPTED_AGE_KEY_PATH="$master_key_path"
    echo "[ℹ️] Використовується незашифрований ключ: '$DECRYPTED_AGE_KEY_PATH'."
    return 0
  fi
}

# Function to clean up the temporary decrypted key file
cleanup_temp_key() {
  if [ -n "$TEMP_KEY_FILE_PATH" ] && [ -f "$TEMP_KEY_FILE_PATH" ]; then
    echo "[🗑️] Безпечне видалення тимчасового файлу ключа '$TEMP_KEY_FILE_PATH'..."
    if shred -u "$TEMP_KEY_FILE_PATH"; then # Використовуємо shred для безпеки
        echo "[✅] Тимчасовий файл ключа видалено."
    else
        echo "[⚠️] ПОМИЛКА безпечного видалення тимчасового файлу ключа '$TEMP_KEY_FILE_PATH'! Будь ласка, видаліть його вручну!"
    fi
    TEMP_KEY_FILE_PATH="" # Скидаємо
  fi
}
# --- Кінець функцій для роботи з ключем ---

# Встановлюємо trap для очищення тимчасового ключа при виході або помилці
trap cleanup_temp_key EXIT SIGINT SIGTERM

cd "$REPO_DIR" # Переконуємось, що ми в корені репозиторію

# Завантажуємо конфігурацію, якщо є .env
if [ -f ".env" ]; then
  # source .env # Небезпечно, якщо .env містить команди
  # Читаємо змінні безпечно
  MASTER_AGE_KEY_STORAGE_PATH=$(grep '^MASTER_AGE_KEY_STORAGE_PATH=' .env | cut -d'=' -f2 | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//')
  EDITOR_FROM_ENV=$(grep '^EDITOR=' .env | cut -d'=' -f2 | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//')
  # Якщо EDITOR не встановлено в .env, використовуємо системний $EDITOR
  EDITOR="${EDITOR_FROM_ENV:-$EDITOR}"

else
  echo "[❌] Файл конфігурації .env не знайдено в корені репозиторію ($REPO_DIR)."
  echo "[ℹ️] Будь ласка, створіть .env з .env.example та налаштуйте його."
  exit 1
fi

# Перевірка наявності MASTER_AGE_KEY_STORAGE_PATH
if [ -z "$MASTER_AGE_KEY_STORAGE_PATH" ]; then
  echo "[❌] Змінна MASTER_AGE_KEY_STORAGE_PATH не визначена у файлі .env."
  exit 1
fi

# Отримуємо шлях до розшифрованого ключа (можливо, тимчасового)
if ! get_decrypted_age_key "$MASTER_AGE_KEY_STORAGE_PATH"; then
  # Повідомлення про помилку вже було виведено функцією
  exit 1
fi
# Тепер змінна DECRYPTED_AGE_KEY_PATH містить шлях до ключа, який можна використовувати з age

# Перевірка, чи встановлено fzf
if ! command -v fzf &> /dev/null; then
    echo "[❌] Команду fzf не знайдено. Будь ласка, встановіть fzf."
    echo "[💡] Ви можете розшифрувати файли вручну командою: age -d -i '$DECRYPTED_AGE_KEY_PATH' -o <вихідний_файл.md> <вхідний_файл.md.age>"
    exit 1
fi

echo "[🔎] Пошук зашифрованих файлів (*.md.age)..."
mapfile -t FILES_TO_DECRYPT < <(find . -maxdepth 1 -type f -name "*.md.age" -print0 | fzf --read0 -m --prompt="Виберіть файли для розшифрування (Tab для вибору кількох, Enter для підтвердження):" --preview "age -d -i '$DECRYPTED_AGE_KEY_PATH' -o /dev/stdout {} 2>/dev/null | head -n 20")

if [ ${#FILES_TO_DECRYPT[@]} -eq 0 ]; then
  echo "[ℹ️] Файли не вибрано. Завершення."
  exit 0 # Вихід без помилки, cleanup_temp_key виконається через trap
fi

echo "[⏳] Розшифрування вибраних файлів..."
SUCCESS_COUNT=0
FAIL_COUNT=0
DECRYPTED_FILES_LIST=()

for ENCRYPTED_FILE_PATH_RAW in "${FILES_TO_DECRYPT[@]}"; do
  # Обробка шляху, якщо find повертає ./file.md.age
  ENCRYPTED_FILE_PATH="${ENCRYPTED_FILE_PATH_RAW#./}"
  ENCRYPTED_FILE_BASENAME=$(basename "$ENCRYPTED_FILE_PATH")
  DECRYPTED_FILE_BASENAME="${ENCRYPTED_FILE_BASENAME%.age}"

  if [ -f "$DECRYPTED_FILE_BASENAME" ]; then
    read -r -p "[⚠️] Файл '$DECRYPTED_FILE_BASENAME' вже існує. Перезаписати? (y/N): " choice
    case "$choice" in
      y|Y ) echo "[ℹ️] Перезаписую $DECRYPTED_FILE_BASENAME...";;
      * ) echo "[ℹ️] Пропускаю розшифрування $ENCRYPTED_FILE_BASENAME."; continue;;
    esac
  fi

  echo "[🔑] Розшифровую $ENCRYPTED_FILE_BASENAME → $DECRYPTED_FILE_BASENAME"
  if age -d -i "$DECRYPTED_AGE_KEY_PATH" -o "$DECRYPTED_FILE_BASENAME" "$ENCRYPTED_FILE_PATH"; then
    echo "[✅] Файл $DECRYPTED_FILE_BASENAME успішно розшифровано."
    DECRYPTED_FILES_LIST+=("$DECRYPTED_FILE_BASENAME")
    ((SUCCESS_COUNT++))
  else
    echo "[❌] Помилка під час розшифрування $ENCRYPTED_FILE_BASENAME."
    [ -f "$DECRYPTED_FILE_BASENAME" ] && rm -f "$DECRYPTED_FILE_BASENAME"
    ((FAIL_COUNT++))
  fi
done

echo ""
echo "[📊] Результат розшифрування:"
echo "    Успішно: $SUCCESS_COUNT"
echo "    З помилками: $FAIL_COUNT"

if [ ${#DECRYPTED_FILES_LIST[@]} -gt 0 ]; then
  echo ""
  echo "[❗] ВАЖЛИВО: Наступні файли було розшифровано і вони зараз знаходяться на диску у відкритому вигляді:"
  for df in "${DECRYPTED_FILES_LIST[@]}"; do
    echo "    - $df"
  done
  echo "[🔒] Не забудьте зашифрувати їх назад після завершення роботи за допомогою 'scripts/encrypt-n-store.sh' або 'scripts/encrypt-unencrypted.sh'!"
  echo "     Розшифровані файли додано до .gitignore, але їх слід видалити/зашифрувати якомога швидше."

  if [ -n "$EDITOR" ] && [ ${#DECRYPTED_FILES_LIST[@]} -le 5 ]; then # Трохи збільшив ліміт
    read -r -p "[❓] Відкрити розшифровані файли в '$EDITOR'? (y/N): " open_choice
    case "$open_choice" in
      y|Y ) $EDITOR "${DECRYPTED_FILES_LIST[@]}";;
      * ) ;;
    esac
  elif [ -n "$EDITOR" ]; then
    echo "[ℹ️] Забагато файлів для автоматичного відкриття. Відкрийте їх вручну: ${DECRYPTED_FILES_LIST[*]}"
  fi
fi

# cleanup_temp_key буде викликано автоматично через trap EXIT
echo "[🚪] Завершення роботи decrypt-n-work.sh."