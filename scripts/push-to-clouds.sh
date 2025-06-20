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
  CLOUD_REMOTES=$(grep '^CLOUD_REMOTES=' .env | cut -d'=' -f2 | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//')
else
  echo "[❌] Файл конфігурації .env не знайдено в корені репозиторію ($REPO_DIR)."
  echo "[ℹ️] Будь ласка, створіть .env з .env.example та налаштуйте його."
  exit 1
fi

# Перевірка наявності публічного ключа отримувача
if [ -z "$AGE_RECIPIENT" ]; then
  echo "[❌] Змінна AGE_RECIPIENT не визначена у файлі .env або порожня."
  echo "[ℹ️] Будь ласка, встановіть AGE_RECIPIENT у файлі .env."
  exit 1
fi

# Перевірка, чи встановлено rclone
if ! command -v rclone &> /dev/null; then
    echo "[❌] Команду rclone не знайдено. Будь ласка, встановіть rclone та налаштуйте ваші хмарні сховища."
    exit 1
fi

# Перевірка, чи визначено CLOUD_REMOTES
if [ -z "$CLOUD_REMOTES" ]; then
  echo "[ℹ️] Змінна CLOUD_REMOTES не визначена або порожня у файлі .env."
  echo "[☁️] Хмарне резервне копіювання буде пропущено."
  exit 0 # Виходимо без помилки, оскільки це опціональна функція
fi

BACKUP_SUBDIR="backup" # Піддиректорія для локальних архівів у корені репо
mkdir -p "$BACKUP_SUBDIR"

DATE_SUFFIX=$(date +"%Y-%m-%d-%H%M%S") # Додав секунди для більшої унікальності
ARCHIVE_BASENAME="secure-repo-backup-$DATE_SUFFIX"
LOCAL_TAR_ARCHIVE_PATH="$BACKUP_SUBDIR/$ARCHIVE_BASENAME.tar.gz"
LOCAL_ENCRYPTED_ARCHIVE_PATH="$BACKUP_SUBDIR/$ARCHIVE_BASENAME.tar.gz.age"

echo "[📦] Підготовка списку файлів для архівування..."
FILES_TO_ARCHIVE=()
# Додаємо README.md, якщо він існує
[ -f "README.md" ] && FILES_TO_ARCHIVE+=("README.md")

# Додаємо всі .md.age файли
# Використовуємо find для надійного збору .md.age файлів з кореневої директорії
# find . -maxdepth 1 -name '*.md.age' -print0 | xargs -0 -I {} FILES_TO_ARCHIVE+=("{}") # Не зовсім так для масивів
# Краще так:
while IFS= read -r -d $'\0' file; do
  FILES_TO_ARCHIVE+=("${file#./}") # Видаляємо можливий ./ на початку
done < <(find . -maxdepth 1 -type f -name "*.md.age" -print0)

# Додаємо директорію .git, якщо вона існує (важливо для повного бекапу репозиторію)
[ -d ".git" ] && FILES_TO_ARCHIVE+=(".git")

if [ ${#FILES_TO_ARCHIVE[@]} -eq 0 ]; then
    echo "[⚠️] Немає файлів для архівування (README.md, *.md.age, .git). Пропускаю створення та завантаження архіву."
    exit 0
fi
echo "[ℹ️] Файли для архівування: ${FILES_TO_ARCHIVE[*]}"


echo "[📦] Створення локального архіву: $LOCAL_TAR_ARCHIVE_PATH..."
# Використовуємо --transform для видалення початкових './' якщо вони є, та для загальної чистоти
# tar -czf "$LOCAL_TAR_ARCHIVE_PATH" --transform='s|^\./||g' "${FILES_TO_ARCHIVE[@]}"
# Або, якщо ми впевнені, що шляхи чисті (без ./), то просто:
if tar czf "$LOCAL_TAR_ARCHIVE_PATH" "${FILES_TO_ARCHIVE[@]}"; then
  echo "[✅] Локальний архів '$LOCAL_TAR_ARCHIVE_PATH' створено."
else
  echo "[❌] Помилка створення локального архіву '$LOCAL_TAR_ARCHIVE_PATH'."
  [ -f "$LOCAL_TAR_ARCHIVE_PATH" ] && rm -f "$LOCAL_TAR_ARCHIVE_PATH"
  exit 1
fi

echo "[🔐] Шифрування архіву за допомогою age: $LOCAL_ENCRYPTED_ARCHIVE_PATH..."
if age -r "$AGE_RECIPIENT" -o "$LOCAL_ENCRYPTED_ARCHIVE_PATH" "$LOCAL_TAR_ARCHIVE_PATH"; then
  echo "[✅] Архів '$LOCAL_ENCRYPTED_ARCHIVE_PATH' успішно зашифровано."
else
  echo "[❌] Помилка шифрування архіву '$LOCAL_TAR_ARCHIVE_PATH'."
  [ -f "$LOCAL_ENCRYPTED_ARCHIVE_PATH" ] && rm -f "$LOCAL_ENCRYPTED_ARCHIVE_PATH"
  [ -f "$LOCAL_TAR_ARCHIVE_PATH" ] && rm -f "$LOCAL_TAR_ARCHIVE_PATH" # Також видаляємо оригінальний tar
  exit 1
fi

echo "[🗑️] Безпечне видалення незашифрованого локального архіву '$LOCAL_TAR_ARCHIVE_PATH'..."
if shred -u "$LOCAL_TAR_ARCHIVE_PATH"; then
  echo "[✅] Незашифрований архів видалено."
else
  echo "[❌] Помилка безпечного видалення '$LOCAL_TAR_ARCHIVE_PATH'! Будь ласка, видаліть його вручну та безпечно."
  # Не виходимо, бо зашифрований архів вже є, але це попередження
fi

# Розбиваємо CLOUD_REMOTES на масив
IFS=' ' read -r -a REMOTES_ARRAY <<< "$CLOUD_REMOTES"

UPLOAD_SUCCESS_COUNT=0
UPLOAD_FAIL_COUNT=0

echo "[☁️] Початок завантаження на хмарні сховища..."
for remote_target in "${REMOTES_ARRAY[@]}"; do
  # remote_target може бути просто "myremote:" або "myremote:path/to/dir"
  # rclone copy source remote:destination_path
  echo "    [🚀] Завантаження '$LOCAL_ENCRYPTED_ARCHIVE_PATH' на '$remote_target'..."
  if rclone copy "$LOCAL_ENCRYPTED_ARCHIVE_PATH" "$remote_target" --progress; then
    echo "    [✅] Успішно завантажено на $remote_target."
    ((UPLOAD_SUCCESS_COUNT++))
  else
    echo "    [❌] Помилка завантаження на $remote_target."
    ((UPLOAD_FAIL_COUNT++))
  fi
done

echo ""
echo "[📊] Результат завантаження бекапів на хмарні сховища:"
echo "    Успішно завантажено на: $UPLOAD_SUCCESS_COUNT сховищ."
if [ $UPLOAD_FAIL_COUNT -gt 0 ]; then
  echo "    [❗] Не вдалося завантажити на: $UPLOAD_FAIL_COUNT сховищ."
  echo "        Перевірте налаштування rclone та доступ до відповідних remote."
fi

if [ $UPLOAD_SUCCESS_COUNT -gt 0 ] && [ $UPLOAD_FAIL_COUNT -eq 0 ]; then
    echo "[👍] Резервне копіювання на всі хмарні сховища завершено успішно."
elif [ $UPLOAD_SUCCESS_COUNT -gt 0 ]; then
    echo "[👍] Резервне копіювання на хмару частково успішне (на $UPLOAD_SUCCESS_COUNT з ${#REMOTES_ARRAY[@]} сховищ)."
else
    echo "[👎] Не вдалося завантажити бекап на жодне хмарне сховище."
    if [ ${#REMOTES_ARRAY[@]} -gt 0 ]; then # Якщо були сконфігуровані ремоути
        exit 1 # Повертаємо помилку, якщо жодне завантаження не вдалося
    fi
fi

# Локальний зашифрований бекап залишається в папці backup/.
echo "[ℹ️] Локальний зашифрований бекап збережено в: $LOCAL_ENCRYPTED_ARCHIVE_PATH"