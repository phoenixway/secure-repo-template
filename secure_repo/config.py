import os
from dotenv import load_dotenv

# Завантажуємо змінні з .env файлу в оточення
load_dotenv()

# Читаємо змінні, надаючи значення за замовчуванням
# Логіка конфігурації взята з .env.example
AGE_RECIPIENT = os.getenv("AGE_RECIPIENT")
MASTER_KEY_PATH = os.getenv("MASTER_AGE_KEY_STORAGE_PATH")
CLOUD_REMOTES = os.getenv("CLOUD_REMOTES", "").split()
EDITOR = os.getenv("EDITOR")