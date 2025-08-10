import os
from dotenv import load_dotenv

# Визначаємо базові шляхи відносно кореня проєкту
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_DIR = os.path.join(ROOT_DIR, "config")
VAULT_DIR = os.path.join(ROOT_DIR, "vault")
KEYS_DIR = os.path.join(CONFIG_DIR, "keys")

# Явно вказуємо шлях до .env файлу
ENV_PATH = os.path.join(CONFIG_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

# Читаємо змінні
AGE_RECIPIENT = os.getenv("AGE_RECIPIENT")
MASTER_KEY_PATH = os.getenv("MASTER_AGE_KEY_STORAGE_PATH")

# Обробляємо шлях до ключа: якщо він відносний, робимо його абсолютним від кореня проєкту
if MASTER_KEY_PATH and not os.path.isabs(MASTER_KEY_PATH):
    MASTER_KEY_PATH = os.path.join(ROOT_DIR, MASTER_KEY_PATH)

CLOUD_REMOTES = os.getenv("CLOUD_REMOTES", "").split()
EDITOR = os.getenv("EDITOR")