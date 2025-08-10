import pytest
import shutil
import os
import subprocess
from pathlib import Path # Додаємо імпорт Path
from click.testing import CliRunner
from manager import cli
from src import config

# ВИПРАВЛЕНО: Визначаємо реальний корінь проєкту надійно, один раз на рівні модуля
REAL_PROJECT_ROOT = Path(__file__).parent.parent

@pytest.mark.skipif(
    not all(shutil.which(cmd) for cmd in ["age", "git", "gpg"]),
    reason="Missing executables (age, git, gpg) for E2E tests"
)
def test_full_init_encrypt_decrypt_cycle(tmp_path):
    runner = CliRunner()
    
    with runner.isolated_filesystem(temp_dir=tmp_path) as temp_dir:
        # --- Підготовка середовища ---
        # ВИПРАВЛЕНО: Використовуємо надійний шлях REAL_PROJECT_ROOT
        shutil.copytree(REAL_PROJECT_ROOT / 'src', os.path.join(temp_dir, 'src'))
        shutil.copy(REAL_PROJECT_ROOT / 'manager.py', temp_dir)
        shutil.copy(REAL_PROJECT_ROOT / '.gitignore', temp_dir)
        shutil.copy(REAL_PROJECT_ROOT / 'README.md', temp_dir)
        shutil.copy(REAL_PROJECT_ROOT / 'requirements.txt', temp_dir)

        temp_config_dir = os.path.join(temp_dir, 'config')
        os.makedirs(temp_config_dir)
        shutil.copy(
            REAL_PROJECT_ROOT / 'config' / '.env.example',
            os.path.join(temp_config_dir, '.env.example')
        )
        
        # --- Ініціалізація ---
        result_init = runner.invoke(cli, ['init', 'git'], input='n\n', catch_exceptions=False)
        assert result_init.exit_code == 0, f"Init failed: {result_init.output}"
        assert "Local Git-based vault initialized successfully!" in result_init.output
        
        # --- Шифрування ---
        vault_dir = 'vault'
        os.makedirs(vault_dir, exist_ok=True)
        note_path = os.path.join(vault_dir, 'my_note.md')
        with open(note_path, "w") as f:
            f.write("secret e2e test")
        
        config.clear_config_cache()
        
        result_encrypt = runner.invoke(cli, ['encrypt'], catch_exceptions=False)
        assert result_encrypt.exit_code == 0, f"Encrypt failed: {result_encrypt.output}"
        
        assert not os.path.exists(note_path)
        assert os.path.exists(f"{note_path}.age")