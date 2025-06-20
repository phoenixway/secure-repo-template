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

# Встановлюємо trap для очищення тимчасового ключа та тимчасової директорії відновлення
# Змінна TMP_RESTORE_FULL_PATH буде визначена пізніше
cleanup_all() {
  cleanup_temp_key
  if [ -n "$TMP_RESTORE_FULL_PATH" ] && [ -d "$TMP_RESTORE_FULL_PATH" ]; then
    echo "[🗑️] Видалення тимчасової директорії відновлення '$TMP_RESTORE_FULL_PATH'..."
    rm -rf "$TMP_RESTORE_FULL_PATH"
    echo "[✅] Тимчасову директорію відновлення видалено."
  fi
}
trap cleanup_all EXIT SIGINT SIGTERM


# Завантажуємо конфігурацію, якщо є .env
ENV_FILE_PATH="$REPO_DIR/.env"
if [ -f "$ENV_FILE_PATH" ]; then
  MASTER_AGE_KEY_STORAGE_PATH=$(grep '^MASTER_AGE_KEY_STORAGE_PATH=' "$ENV_FILE_PATH" | cut -d'=' -f2 | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//')
  CLOUD_REMOTES_FROM_ENV=$(grep '^CLOUD_REMOTES=' "$ENV_FILE_PATH" | cut -d'=' -f2 | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//')
else
  echo "[❌] Файл конфігурації '$ENV_FILE_PATH' не знайдено."
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
  exit 1
fi
# Тепер змінна DECRYPTED_AGE_KEY_PATH містить шлях до ключа

# Перевірка, чи встановлено rclone
if ! command -v rclone &> /dev/null; then
    echo "[❌] Команду rclone не знайдено. Будь ласка, встановіть rclone."
    exit 1
fi

# Перевірка, чи визначено CLOUD_REMOTES
if [ -z "$CLOUD_REMOTES_FROM_ENV" ]; then
  echo "[❌] Змінна CLOUD_REMOTES не визначена або порожня у файлі .env."
  echo "[ℹ️] Неможливо вибрати хмарне сховище для відновлення."
  exit 1
fi

# Створюємо унікальну тимчасову директорію в корені репозиторію
# Це дозволить .gitignore ігнорувати її (tmp-restore-*/)
TMP_RESTORE_PARENT_DIR="$REPO_DIR"
TMP_RESTORE_DIR_NAME="tmp-restore-$(date +%Y%m%d-%H%M%S)-$RANDOM"
TMP_RESTORE_FULL_PATH="$TMP_RESTORE_PARENT_DIR/$TMP_RESTORE_DIR_NAME"

mkdir -p "$TMP_RESTORE_FULL_PATH"
echo "[📁] Створено тимчасову директорію для відновлення: $TMP_RESTORE_FULL_PATH"
# Важливо: НЕ робимо cd "$TMP_RESTORE_FULL_PATH" на цьому етапі,
# щоб відносні шляхи до rclone та інші команди працювали з кореня репо, якщо потрібно.
# Або, якщо робимо cd, то всі шляхи мають бути абсолютними або відносними до нової директорії.
# Для простоти, rclone буде завантажувати прямо в $TMP_RESTORE_FULL_PATH


echo "[☁️] Отримання списку доступних хмарних сховищ з .env..."
IFS=' ' read -r -a REMOTES_ARRAY <<< "$CLOUD_REMOTES_FROM_ENV"

if [ ${#REMOTES_ARRAY[@]} -eq 0 ]; then
    echo "[❌] Не знайдено жодного хмарного сховища в CLOUD_REMOTES у файлі .env."
    exit 1
fi

echo "Доступні хмарні сховища для відновлення:"
PS3="Виберіть номер хмарного сховища: "
select remote_choice in "${REMOTES_ARRAY[@]}"; do
  if [[ -n "$remote_choice" ]]; then
    SELECTED_REMOTE="$remote_choice"
    echo "[✅] Вибрано сховище: $SELECTED_REMOTE"
    break
  else
    echo "Неправильний вибір. Спробуйте ще раз."
  fi
done

echo "[🔍] Отримання списку файлів бекапів з '$SELECTED_REMOTE' (тільки .tar.gz.age)..."
# Використовуємо rclone lsf для отримання тільки імен файлів, фільтруємо за допомогою grep
# Це надійніше, ніж ls + awk
BACKUP_FILES_LIST_RAW=$(rclone lsf "$SELECTED_REMOTE" --files-only 2>/dev/null | grep '\.tar\.gz\.age$')

if [ -z "$BACKUP_FILES_LIST_RAW" ]; then
  echo "[❌] Не знайдено файлів бекапів (*.tar.gz.age) на '$SELECTED_REMOTE'."
  exit 1
fi

# Перетворюємо рядок з іменами файлів в масив
mapfile -t BACKUP_FILES_ARRAY < <(echo "$BACKUP_FILES_LIST_RAW")

if [ ${#BACKUP_FILES_ARRAY[@]} -eq 0 ]; then
  echo "[❌] Не знайдено файлів бекапів (*.tar.gz.age) на '$SELECTED_REMOTE' після обробки."
  exit 1
fi

echo "Доступні файли бекапів на '$SELECTED_REMOTE':"
PS3="Виберіть номер файлу бекапу для відновлення: "
select selected_backup_filename in "${BACKUP_FILES_ARRAY[@]}"; do
  if [[ -n "$selected_backup_filename" ]]; then
    echo "[✅] Вибрано файл бекапу: $selected_backup_filename"
    break
  else
    echo "Неправильний вибір. Спробуйте ще раз."
  fi#!/bin/bash
set -e

# Визначаємо директорію скрипта та корінь репозиторію
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# Скрипт працюватиме у власній тимчасовій директорії, але .env та AGE_KEY_FILE беруться з REPO_DIR

# Завантажуємо конфігурацію, якщо є .env
ENV_FILE_PATH="$REPO_DIR/.env"
if [ -f "$ENV_FILE_PATH" ]; then
  # Обережно source .env, щоб не перезаписати змінні скрипта, якщо є конфлікти
  # Краще читати змінні явно
  # source "$ENV_FILE_PATH" # Може бути небезпечно, якщо .env містить команди
  # Читаємо тільки потрібні змінні
  # Використовуємо eval з обережністю або grep
  # grep -E '^(AGE_KEY_FILE|CLOUD_REMOTES)=' "$ENV_FILE_PATH" > /tmp/env_vars.sh
  # source /tmp/env_vars.sh
  # rm /tmp/env_vars.sh
  # Або безпечніше:
  AGE_KEY_FILE_FROM_ENV=$(grep '^AGE_KEY_FILE=' "$ENV_FILE_PATH" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
  CLOUD_REMOTES_FROM_ENV=$(grep '^CLOUD_REMOTES=' "$ENV_FILE_PATH" | cut -d'=' -f2 | sed 's/^"//' | sed 's/"$//' | sed "s/^'//" | sed "s/'$//") # Обробка лапок
else
  echo "[❌] Файл конфігурації '$ENV_FILE_PATH' не знайдено."
  echo "[ℹ️] Будь ласка, створіть .env з .env.example та налаштуйте його."
  exit 1
fi

# Використовуємо змінні, прочитані з .env
AGE_KEY_FILE_ABS_PATH="$REPO_DIR/$AGE_KEY_FILE_FROM_ENV" # Абсолютний шлях до ключа
CLOUD_REMOTES="$CLOUD_REMOTES_FROM_ENV"

# Перевірка наявності шляху до файлу приватного ключа
if [ -z "$AGE_KEY_FILE_FROM_ENV" ]; then # Перевіряємо саме змінну з .env
  echo "[❌] Змінна AGE_KEY_FILE не визначена у файлі .env."
  exit 1
fi

# Перевірка існування самого файлу приватного ключа
if [ ! -f "$AGE_KEY_FILE_ABS_PATH" ]; then
  echo "[❌] Файл приватного ключа '$AGE_KEY_FILE_ABS_PATH' (вказаний як '$AGE_KEY_FILE_FROM_ENV' у .env відносно '$REPO_DIR') не знайдено!"
  exit 1
fi

# Перевірка, чи встановлено rclone
if ! command -v rclone &> /dev/null; then
    echo "[❌] Команду rclone не знайдено. Будь ласка, встановіть rclone."
    exit 1
fi

# Перевірка, чи визначено CLOUD_REMOTES
if [ -z "$CLOUD_REMOTES" ]; then
  echo "[❌] Змінна CLOUD_REMOTES не визначена або порожня у файлі .env."
  echo "[ℹ️] Неможливо вибрати хмарне сховище для відновлення."
  exit 1
fi

TMP_RESTORE_PARENT_DIR="$REPO_DIR" # Де створювати tmp-restore
TMP_RESTORE_DIR_NAME="tmp-restore-$(date +%Y%m%d-%H%M%S)"
TMP_RESTORE_FULL_PATH="$TMP_RESTORE_PARENT_DIR/$TMP_RESTORE_DIR_NAME"

mkdir -p "$TMP_RESTORE_FULL_PATH"
# Переходимо в тимчасову директорію, щоб всі завантажені файли були там
cd "$TMP_RESTORE_FULL_PATH"
echo "[chdir] Робоча директорія для відновлення: $(pwd)"


echo "[☁️] Отримання списку доступних хмарних сховищ з .env..."
# Розбиваємо CLOUD_REMOTES на масив
IFS=' ' read -r -a REMOTES_ARRAY <<< "$CLOUD_REMOTES"

if [ ${#REMOTES_ARRAY[@]} -eq 0 ]; then
    echo "[❌] Не знайдено жодного хмарного сховища в CLOUD_REMOTES у файлі .env."
    exit 1
fi

echo "Доступні хмарні сховища для відновлення:"
PS3="Виберіть номер хмарного сховища: "
select remote_choice in "${REMOTES_ARRAY[@]}"; do
  if [[ -n "$remote_choice" ]]; then
    SELECTED_REMOTE="$remote_choice"
    echo "[✅] Вибрано сховище: $SELECTED_REMOTE"
    break
  else
    echo "Неправильний вибір. Спробуйте
fi
echo "[✅] Архів успішно розшифровано."

# Після успішного розшифрування, зашифрований архів вже не потрібен у тимчасовій директорії
echo "[🗑️] Видалення завантаженого зашифрованого архіву '$DOWNLOADED_ENCRYPTED_ARCHIVE_PATH'..."
rm -f "$DOWNLOADED_ENCRYPTED_ARCHIVE_PATH"


mkdir -p "$EXTRACTED_CONTENT_PATH"
echo "[📦] Розпакування архіву '$DECRYPTED_TAR_ARCHIVE_PATH' до '$EXTRACTED_CONTENT_PATH'..."
if ! tar xzf "$DECRYPTED_TAR_ARCHIVE_PATH" -C "$EXTRACTED_CONTENT_PATH"; then
  echo "[❌] Помилка розпакування архіву."
  exit 1
fi
echo "[✅] Архів успішно розпаковано."

# Після успішного розпакування, розшифрований .tar.gz архів вже не потрібен
echo "[🗑️] Безпечне видалення розшифрованого архіву '$DECRYPTED_TAR_ARCHIVE_PATH'..."
# Використовуємо shred для .tar.gz, оскільки він міг містити незашифровані (хоча і архівовані) дані
if shred -u "$DECRYPTED_TAR_ARCHIVE_PATH"; then
    echo "[✅] Розшифрований архів видалено."
else
    echo "[⚠️] ПОМИЛКА безпечного видалення розшифрованого архіву '$DECRYPTED_TAR_ARCHIVE_PATH'! Будь ласка, видаліть його вручну!"
fi


echo ""
echo "[🎉] Відновлення завершено!"
echo "    Розшифрований та розпакований вміст знаходиться в директорії:"
echo "    $EXTRACTED_CONTENT_PATH"
echo ""
echo "[❗] ВАЖЛИВО: Ознайомтеся з вмістом цієї директорії."
echo "    Скопіюйте потрібні файли до вашого основного репозиторію або іншого безпечного місця."
echo "    Після завершення роботи, ця тимчасова директорія '$TMP_RESTORE_FULL_PATH' буде автоматично видалена при виході зі скрипта."
echo "    Якщо ви хочете зберегти її, скопіюйте її вміст зараз."
read -n 1 -s -r -p "Натисніть будь-яку клавішу для завершення та очищення..."
echo ""

# cleanup_all буде викликано автоматично через trap EXIT
echo "[🚪] Завершення роботи restore-from-cloud.sh."дай повний encrypt-unencrypted.