#!/bin/bash
set -e

# Визначаємо директорію, де знаходиться сам init-secure-repo.sh (директорія шаблону)
TEMPLATE_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_ROOT_DIR="$(cd "$TEMPLATE_SCRIPT_DIR/.." && pwd)"

TARGET_REPO_NAME="$1"
if [ -z "$TARGET_REPO_NAME" ]; then
  echo "🔧 Використання: $0 <назва_нового_репозиторію>"
  echo "Наприклад: $0 my-secret-notes"
  exit 1
fi

if [ -d "$TARGET_REPO_NAME" ]; then
  echo "[❌] Директорія '$TARGET_REPO_NAME' вже існує."
  exit 1
fi

echo "[⚙️] Створення структури репозиторію '$TARGET_REPO_NAME'..."
mkdir -p "$TARGET_REPO_NAME/scripts" "$TARGET_REPO_NAME/personal-scripts" "$TARGET_REPO_NAME/backup"
cd "$TARGET_REPO_NAME"
TARGET_REPO_ABS_PATH=$(pwd)

echo "[📝] Ініціалізація Git репозиторію..."
git init -b main

echo "[📄] Створення README.md..."
cat > README.md <<EOF
# $TARGET_REPO_NAME

Цей репозиторій зберігає зашифровані чутливі дані, використовуючи шаблон secure-repo-template.
EOF

echo "[🙈] Створення .gitignore..."
if [ -f "$TEMPLATE_ROOT_DIR/.gitignore" ]; then
  cp "$TEMPLATE_ROOT_DIR/.gitignore" .
else
  echo "[⚠️] Не вдалося знайти .gitignore в шаблоні. Створюю базовий."
  cat > .gitignore <<EOF
# Розшифровані файли Markdown (крім README.md)
*.md
!README.md

# Приватний ключ age - НІКОЛИ НЕ КОМІТИТИ ПРЯМО!
# Замість цього, він має бути зашифрований (наприклад, age-key.txt.gpg)
# і шлях до нього вказаний в .env (MASTER_AGE_KEY_STORAGE_PATH)
# Сам age-key.txt (нешифрований) має бути доданий в .gitignore, якщо він створюється локально
age-key.txt

# Файл конфігурації середовища - НІКОЛИ НЕ КОМІТИТИ!
.env
.env.*
!.env.example

# Директорія для бекапів (локальних архівів)
backup/

# Директорія для персональних скриптів
personal-scripts/

# Тимчасові файли відновлення
tmp-restore-*/
tmp-restore*/
EOF
fi

echo "[🔑] Генерація нового приватного ключа age..."
# Генеруємо ключ в поточній директорії (корінь нового репо)
# Він буде називатися age-key.txt
age-keygen -o "age-key.txt"
LOCAL_PLAIN_AGE_KEY_FILE="age-key.txt"
MASTER_KEY_PATH_FOR_ENV="$LOCAL_PLAIN_AGE_KEY_FILE" # За замовчуванням, якщо не шифруємо GPG

echo ""
echo "[🛡️] Захист приватного ключа (рекомендовано GPG шифрування):"
echo "    Ваш новий приватний ключ збережено у файлі: $TARGET_REPO_ABS_PATH/$LOCAL_PLAIN_AGE_KEY_FILE"
echo "    ВАЖЛИВО: Цей файл містить ваш секретний ключ! Його слід зберігати максимально безпечно."
echo "    Рекомендується зашифрувати його за допомогою GPG."

GPG_ENCRYPTED_KEY_FILE="${LOCAL_PLAIN_AGE_KEY_FILE}.gpg"
GPG_ENCRYPTION_SUCCESSFUL=false

if command -v gpg &> /dev/null; then
  read -r -p "    [❓] Бажаєте зашифрувати '$LOCAL_PLAIN_AGE_KEY_FILE' за допомогою GPG зараз? (Y/n): " choice
  case "$choice" in
    n|N ) echo "    [ℹ️] Пропускаю GPG шифрування. Переконайтеся, що ви самостійно захистили '$LOCAL_PLAIN_AGE_KEY_FILE'.";;
    * )
      echo "    [🔐] Шифрування '$LOCAL_PLAIN_AGE_KEY_FILE' -> '$GPG_ENCRYPTED_KEY_FILE'..."
      echo "        Введіть надійну парольну фразу для GPG шифрування."
      if gpg --quiet --batch --yes --symmetric --cipher-algo AES256 -o "$GPG_ENCRYPTED_KEY_FILE" "$LOCAL_PLAIN_AGE_KEY_FILE"; then
        echo "    [✅] Файл '$LOCAL_PLAIN_AGE_KEY_FILE' успішно зашифровано як '$GPG_ENCRYPTED_KEY_FILE'."
        echo "        Оригінальний незашифрований файл '$LOCAL_PLAIN_AGE_KEY_FILE' буде видалено."
        if shred -u "$LOCAL_PLAIN_AGE_KEY_FILE"; then
          echo "    [🗑️] Оригінальний файл '$LOCAL_PLAIN_AGE_KEY_FILE' безпечно видалено."
        else
          echo "    [⚠️] ПОМИЛКА безпечного видалення '$LOCAL_PLAIN_AGE_KEY_FILE'! Будь ласка, видаліть його вручну!"
        fi
        MASTER_KEY_PATH_FOR_ENV="$GPG_ENCRYPTED_KEY_FILE"
        GPG_ENCRYPTION_SUCCESSFUL=true
      else
        echo "    [❌] Помилка GPG шифрування. Незашифрований ключ '$LOCAL_PLAIN_AGE_KEY_FILE' залишено."
        echo "        Перевірте налаштування GPG або спробуйте пізніше."
      fi
      ;;
  esac
else
  echo "    [ℹ️] GPG не встановлено. Шифрування ключа за допомогою GPG пропущено."
  echo "        Настійно рекомендується встановити GPG та зашифрувати '$LOCAL_PLAIN_AGE_KEY_FILE' вручну:"
  echo "        gpg --symmetric --cipher-algo AES256 -o ${GPG_ENCRYPTED_KEY_FILE} ${LOCAL_PLAIN_AGE_KEY_FILE}"
  echo "        Після цього не забудьте безпечно видалити оригінальний ${LOCAL_PLAIN_AGE_KEY_FILE} (shred -u ${LOCAL_PLAIN_AGE_KEY_FILE})"
fi

echo ""
echo "[🔑] Отримання публічного ключа age..."
# Отримуємо публічний ключ з того файлу, який є актуальним (зашифрований або ні)
# Якщо GPG шифрування було успішним, MASTER_KEY_PATH_FOR_ENV вказує на .gpg файл
AGE_PUBLIC_KEY=""
KEY_SOURCE_FOR_PUBLIC_KEY="$MASTER_KEY_PATH_FOR_ENV" # Або, якщо GPG, то з розшифрованого потоку

if $GPG_ENCRYPTION_SUCCESSFUL; then
    echo "    (Отримання публічного ключа з тимчасово розшифрованого GPG-файла)"
    # Потрібно запитати пароль знову, або тимчасово розшифрувати
    # Для простоти ініціалізації, якщо ключ зашифровано, попросимо користувача ввести його вручну
    # або надамо команду. Інакше це ускладнить init скрипт.
    # Краще: якщо GPG було щойно зроблено, gpg може все ще мати ключ сесії, спробуємо:
    if ! AGE_PUBLIC_KEY=$(gpg --quiet --batch --yes --decrypt "$MASTER_KEY_PATH_FOR_ENV" 2>/dev/null | age-keygen -y - 2>/dev/null); then
        echo "    [⚠️] Не вдалося автоматично отримати публічний ключ з '$MASTER_KEY_PATH_FOR_ENV'."
        echo "        Якщо файл зашифровано GPG, це могло статися через кешування пароля GPG."
    fi
else # Ключ не шифрувався GPG або шифрування не вдалося, використовуємо plain файл
    if [ -f "$LOCAL_PLAIN_AGE_KEY_FILE" ]; then # Перевіряємо, чи він ще існує
        AGE_PUBLIC_KEY=$(age-keygen -y "$LOCAL_PLAIN_AGE_KEY_FILE")
    fi
fi

if [ -z "$AGE_PUBLIC_KEY" ]; then
    echo "    [❌] НЕ ВДАЛОСЯ АВТОМАТИЧНО ОТРИМАТИ ПУБЛІЧНИЙ КЛЮЧ AGE."
    echo "    Будь ласка, отримайте його вручну та вставте в .env файл у змінну AGE_RECIPIENT."
    echo "    Команда для отримання (якщо ключ в $LOCAL_PLAIN_AGE_KEY_FILE): age-keygen -y $LOCAL_PLAIN_AGE_KEY_FILE"
    echo "    Команда (якщо ключ в $GPG_ENCRYPTED_KEY_FILE): gpg -d $GPG_ENCRYPTED_KEY_FILE | age-keygen -y -"
fi

echo "[ℹ️] Ваш публічний ключ (recipient): $AGE_PUBLIC_KEY"
echo "    (Його буде автоматично додано до .env, якщо вдалося отримати)"


echo "[⚙️] Створення файлу .env з .env.example..."
ENV_EXAMPLE_PATH="$TEMPLATE_ROOT_DIR/.env.example"
if [ ! -f "$ENV_EXAMPLE_PATH" ]; then
    echo "[❌] Фатальна помилка: файл шаблону .env.example не знайдено в '$ENV_EXAMPLE_PATH'."
    exit 1
fi
cp "$ENV_EXAMPLE_PATH" .env

# Оновлюємо .env: MASTER_AGE_KEY_STORAGE_PATH та AGE_RECIPIENT
# Використовуємо sed. Для крос-платформенності з macOS/BSD sed -i ''
# Оскільки ми в Linux середовищі (судячи з шляхів), простий sed -i підійде.
# Якщо потрібна крос-платформенність, можна використовувати awk або perl.

# Замінюємо MASTER_AGE_KEY_STORAGE_PATH
# Використовуємо # як роздільник в sed, бо шляхи можуть містити /
ESCAPED_MASTER_KEY_PATH_FOR_ENV=$(printf '%s\n' "$MASTER_KEY_PATH_FOR_ENV" | sed 's/[\&/]/\\&/g') # Екрануємо / та &
sed -i "s#^MASTER_AGE_KEY_STORAGE_PATH=.*#MASTER_AGE_KEY_STORAGE_PATH=\"$ESCAPED_MASTER_KEY_PATH_FOR_ENV\"#" .env

# Замінюємо AGE_RECIPIENT
if [ -n "$AGE_PUBLIC_KEY" ]; then
  ESCAPED_AGE_PUBLIC_KEY=$(printf '%s\n' "$AGE_PUBLIC_KEY" | sed 's/[\&/]/\\&/g')
  sed -i "s#^AGE_RECIPIENT=.*#AGE_RECIPIENT=\"$ESCAPED_AGE_PUBLIC_KEY\"#" .env
else
  echo "[⚠️] Публічний ключ AGE_RECIPIENT не було автоматично встановлено в .env. Будь ласка, додайте його вручну."
fi

echo "[ℹ️] Файл .env створено та оновлено."
echo "    Будь ласка, перевірте .env та заповніть CLOUD_REMOTES, якщо потрібно."

echo "[📜] Копіювання скриптів автоматизації..."
SCRIPTS_TO_COPY=(
  "decrypt-n-work.sh"
  "encrypt-n-store.sh"
  "encrypt-unencrypted.sh"
  "push-to-clouds.sh"
  "restore-from-cloud.sh"
)
# Видаляємо старий backup-to-cloud.sh, якщо він був у шаблоні
# rm -f "$TEMPLATE_SCRIPT_DIR/backup-to-cloud.sh" # Якщо він там є і його треба прибрати з самого шаблону

for script_name in "${SCRIPTS_TO_COPY[@]}"; do
  if [ -f "$TEMPLATE_SCRIPT_DIR/$script_name" ]; then
    cp "$TEMPLATE_SCRIPT_DIR/$script_name" "scripts/"
    chmod +x "scripts/$script_name"
  else
    echo "[⚠️] Увага: Скрипт '$script_name' не знайдено в '$TEMPLATE_SCRIPT_DIR'."
  fi
done

echo ""
echo "[🎉] Готово! Створено укріплений репозиторій '$TARGET_REPO_NAME' в $TARGET_REPO_ABS_PATH"
echo ""
echo "Важливі наступні кроки:"
echo "1.  Переконайтеся, що ви надійно зберегли парольну фразу для GPG (якщо ви шифрували ключ)."
echo "2.  Якщо ви НЕ шифрували ключ '$LOCAL_PLAIN_AGE_KEY_FILE' за допомогою GPG, зробіть це зараз вручну або перемістіть його в ДУЖЕ безпечне місце."
echo "    Шлях до вашого основного приватного ключа (зашифрованого чи ні) має бути правильно вказаний у файлі .env в змінній MASTER_AGE_KEY_STORAGE_PATH."
echo "    Поточне значення в .env: MASTER_AGE_KEY_STORAGE_PATH=\"$MASTER_KEY_PATH_FOR_ENV\""
echo "3.  Перевірте файл .env:"
echo "    - Переконайтеся, що AGE_RECIPIENT встановлено правильно (ваш публічний ключ)."
echo "    - Заповніть CLOUD_REMOTES, якщо плануєте використовувати хмарні бекапи."
echo "4.  Зробіть перший коміт: "
echo "    git add .gitignore README.md .env.example scripts/"
echo "    # Перевірте, чи потрібно додавати .env (якщо ви його налаштували і хочете його версіонувати ЛОКАЛЬНО - не для push!)"
echo "    # АБО КРАЩЕ: git add . (якщо .gitignore налаштований правильно і не закоммітить секрети)"
echo "    git commit -m \"Initial setup of secure repository $TARGET_REPO_NAME\""
echo "5.  (Опціонально) Підключіть до віддаленого Git репозиторію та зробіть push."
echo "    Приклад для GitHub (використовуючи GitHub CLI):"
echo "    gh repo create $TARGET_REPO_NAME --private --source=. --remote=origin --push"
echo ""
echo "Безпека вашого приватного ключа - ваша відповідальність!"
