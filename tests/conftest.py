import pytest
from click.testing import CliRunner
from src import config # Імпортуємо наш конфіг

@pytest.fixture
def runner():
    """Фікстура для тестування Click CLI."""
    return CliRunner()

@pytest.fixture
def setup_fs(fs, mocker): # Додаємо mocker до фікстури
    """
    Створює віртуальну ФС ТА підміняє константи шляхів у `src.config`
    для роботи в ізольованому середовищі.
    """
    # 1. Створюємо віртуальні директорії
    fs.create_dir("/vault")
    fs.create_dir("/config/keys")
    
    # 2. Підміняємо ("мокаємо") константи шляхів у модулі config
    mocker.patch.object(config, 'ROOT_DIR', '/')
    mocker.patch.object(config, 'VAULT_DIR', '/vault')
    mocker.patch.object(config, 'CONFIG_DIR', '/config')
    mocker.patch.object(config, 'KEYS_DIR', '/config/keys')
    mocker.patch.object(config, 'ENV_PATH', '/config/.env')
    
    # 3. Створюємо базові файли у віртуальній ФС
    fs.create_file("/config/.env.example", contents="AGE_RECIPIENT=\nMASTER_AGE_KEY_STORAGE_PATH=\n")
    fs.create_file("/README.md", contents="# Test Repo")
    fs.create_dir("/.git")

    # Ця фікстура нічого не повертає, вона лише налаштовує середовище