import os
from dotenv import load_dotenv

def get_root_dir():
    """Повертає поточну робочу директорію."""
    return os.getcwd()

def get_config_dir():
    return os.path.join(get_root_dir(), "config")

def get_vault_dir():
    return os.path.join(get_root_dir(), "vault")

def get_keys_dir():
    return os.path.join(get_config_dir(), "keys")

def get_env_path():
    return os.path.join(get_config_dir(), ".env")

_config_cache = {}

def load_config():
    """Завантажує змінні з .env файлу і кешує їх."""
    global _config_cache
    if _config_cache:
        return

    load_dotenv(dotenv_path=get_env_path())
    
    master_key_path = os.getenv("MASTER_AGE_KEY_STORAGE_PATH")
    if master_key_path and not os.path.isabs(master_key_path):
        master_key_path = os.path.join(get_root_dir(), master_key_path)

    _config_cache = {
        "AGE_RECIPIENT": os.getenv("AGE_RECIPIENT"),
        "MASTER_KEY_PATH": master_key_path,
        "CLOUD_REMOTES": os.getenv("CLOUD_REMOTES", "").split(),
        "EDITOR": os.getenv("EDITOR"),
    }

def get_config(key):
    """Повертає значення конфігурації. Завантажує, якщо потрібно."""
    if not _config_cache:
        load_config()
    return _config_cache.get(key)

def clear_config_cache():
    """Очищує кеш конфігурації. Потрібно для тестів."""
    global _config_cache
    _config_cache = {}