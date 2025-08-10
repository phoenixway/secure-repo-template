import pytest
import shutil
import os
import subprocess
from click.testing import CliRunner
from manager import cli
from src import config
from pathlib import Path # Додаємо імпорт Path

# ВИПРАВЛЕНО: Визначаємо реальний корінь проєкту надійно, один раз
# Path(__file__) -> шлях до поточного файлу (test_e2e.py)
# .parent -> tests/
# .parent -> корінь проєкту
REAL_PROJECT_ROOT = Path(__file__).parent.parent

@pytest.mark.skipif(
    not all(shutil.which(cmd) for cmd in ["age", "git", "gpg"]),
    reason="Missing executables (age, git, gpg) for E2E tests"
)
def test_full_init_encrypt_decrypt_cycle(tmp_path):
    """
    Тестує повний життєвий цикл як окремі, ізольовані запуски.
    """
    runner = CliRunner()
    
    # Використовуємо runner.isolated_filesystem, який автоматично переходить (cd) в tmp_path
    with runner.isolated_filesystem(temp_dir=tmp_path) as temp_dir:
        
        # --- Крок 1: Підготовка середовища ---
        # Копіюємо вихідний код та конфігурацію, використовуючи надійний шлях
        shutil.copytree(REAL_PROJECT_ROOT / 'src', os.path.join(temp_dir, 'src'))
        shutil.copy(REAL_PROJECT_ROOT / 'manager.py', temp_dir)
        
        temp_config_dir = os.path.join(temp_dir, 'config')
        os.makedirs(temp_config_dir)
        shutil.copy(
            REAL_PROJECT_ROOT / 'config' / '.env.example',
            os.path.join(temp_config_dir, '.env.example')
        )
        
        # Копіюємо решту файлів, потрібних для першого коміту
        shutil.copy(REAL_PROJECT_ROOT / '.gitignore', temp_dir)
        shutil.copy(REAL_PROJECT_ROOT / 'README.md', temp_dir)
        shutil.copy(REAL_PROJECT_ROOT / 'requirements.txt', temp_dir)
        
        subprocess.run(["git", "init"], capture_output=True, text=True)

        # --- Крок 2: Ініціалізація ---
        result_init = runner.invoke(cli, ['init'], input='n\n', catch_exceptions=False)
        assert result_init.exit_code == 0, f"Init failed: {result_init.output}"
        assert "Initialization complete!" in result_init.output
        
        # --- Крок 3: Шифрування ---
        vault_dir = 'vault'
        os.makedirs(vault_dir, exist_ok=True)
        note_path = os.path.join(vault_dir, 'my_note.md')
        with open(note_path, "w") as f:
            f.write("secret e2e test")
        
        # Очищуємо кеш конфігу, щоб підхопити новий .env
        config.clear_config_cache()
        
        result_encrypt = runner.invoke(cli, ['encrypt'], catch_exceptions=False)
        assert result_encrypt.exit_code == 0, f"Encrypt failed: {result_encrypt.output}"
        
        assert not os.path.exists(note_path)
        assert os.path.exists(f"{note_path}.age")