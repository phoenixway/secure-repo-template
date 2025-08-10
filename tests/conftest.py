import pytest
from click.testing import CliRunner
from src import config

@pytest.fixture
def runner():
    """Фікстура для тестування Click CLI."""
    return CliRunner()

@pytest.fixture
def setup_fs(fs, mocker):
    """
    Створює віртуальну ФС, підміняє шляхи в `src.config`
    і повертає об'єкт файлової системи `fs` для подальшого використання.
    """
    fs.create_dir("/vault")
    fs.create_dir("/config/keys")
    
    mocker.patch('src.config.get_root_dir', return_value='/')
    mocker.patch('src.config.get_vault_dir', return_value='/vault')
    mocker.patch('src.config.get_config_dir', return_value='/config')
    mocker.patch('src.config.get_keys_dir', return_value='/config/keys')
    mocker.patch('src.config.get_env_path', return_value='/config/.env')
    
    fs.create_file("/config/.env.example", contents="AGE_RECIPIENT=\nMASTER_AGE_KEY_STORAGE_PATH=\n")
    fs.create_file("/README.md", contents="# Test Repo")
    fs.create_dir("/.git")
    
    # ВИПРАВЛЕНО: Повертаємо об'єкт fs
    return fs