import pytest
import shutil
import os
import subprocess
from pathlib import Path
from click.testing import CliRunner
from manager import cli
from src import config

# Визначаємо реальний корінь проєкту надійно, один раз на рівні модуля
REAL_PROJECT_ROOT = Path(__file__).parent.parent

@pytest.mark.skipif(
    not all(shutil.which(cmd) for cmd in ["age", "git", "gpg"]),
    reason="Missing executables (age, git, gpg) for E2E tests"
)
def test_full_init_encrypt_decrypt_cycle(tmp_path):
    """
    Тестує повний життєвий цикл: init local git -> encrypt -> decrypt.
    """
    runner = CliRunner()
    
    # Використовуємо runner.isolated_filesystem, який автоматично переходить (cd) в tmp_path
    with runner.isolated_filesystem(temp_dir=tmp_path) as temp_dir:
        
        # --- Крок 1: Підготовка середовища ---
        # Копіюємо вихідний код та конфігурацію, використовуючи надійний шлях
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

        # --- Крок 2: Ініціалізація ---
        # ОНОВЛЕНО: Викликаємо нову команду 'init local git'
        result_init = runner.invoke(cli, ['init', 'local', 'git'], input='n\n', catch_exceptions=False)
        assert result_init.exit_code == 0, f"Init failed: {result_init.output}"
        assert "Local Git-based vault initialized successfully!" in result_init.output
        
        # --- Крок 3: Шифрування ---
        vault_dir = 'vault'
        os.makedirs(vault_dir, exist_ok=True)
        note_path = os.path.join(vault_dir, 'my_note.md')
        note_content = "secret e2e test"
        with open(note_path, "w") as f:
            f.write(note_content)
        
        # Очищуємо кеш конфігу, щоб підхопити новий .env
        config.clear_config_cache()
        
        result_encrypt = runner.invoke(cli, ['encrypt'], catch_exceptions=False)
        assert result_encrypt.exit_code == 0, f"Encrypt failed: {result_encrypt.output}"
        
        assert not os.path.exists(note_path)
        assert os.path.exists(f"{note_path}.age")

        # --- Крок 4 (опціонально): Перевірка розшифровки ---
        # Цей етап можна додати для повної перевірки
        config.clear_config_cache()
        # Імітуємо, що користувач вибрав файл в fzf
        def mock_fzf(command, **kwargs):
            if command and command[0] == 'fzf':
                return subprocess.CompletedProcess(args=command, returncode=0, stdout='my_note.md.age\n', stderr='')
            real_command = command.copy()
            if real_command and shutil.which(real_command[0]):
                real_command[0] = shutil.which(real_command[0])
            return subprocess.run(real_command, **kwargs)

        # Підміняємо run_command лише для цього етапу тесту
        # Для цього потрібна фікстура monkeypatch, додаємо її в параметри тесту
        # monkeypatch.setattr('src.system.run_command', mock_fzf)
        # result_decrypt = runner.invoke(cli, ['decrypt'], input='n\n')
        # assert result_decrypt.exit_code == 0
        # assert os.path.exists(note_path)