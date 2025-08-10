import pytest
from click.testing import CliRunner

@pytest.fixture
def runner():
    """Фікстура для тестування Click CLI."""
    return CliRunner()

@pytest.fixture
def setup_fs(fs):
    """
    Фікстура, що використовує pyfakefs (fs) для створення
    базової структури файлів перед кожним тестом.
    """
    # fs - це магічна фікстура від pyfakefs, яка створює віртуальну ФС
    fs.create_file(".env.example", contents="AGE_RECIPIENT=\nMASTER_AGE_KEY_STORAGE_PATH=\n")
    fs.create_file("README.md", contents="# Test Repo")
    # Створюємо фейковий Git-репозиторій
    fs.create_dir(".git")