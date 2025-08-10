from src import initializer, vcs
import os

# Цей тест вже проходить
def test_run_initialization_success_no_gpg(mocker, setup_fs):
    """Тестує успішний сценарій ініціалізації БЕЗ шифрування GPG."""
    mock_run_command = mocker.patch('src.system.run_command')
    mocker.patch('src.system.check_dependencies', return_value=True)
    mocker.patch('src.ui.prompt_yes_no', return_value=False)
    mocker.patch('src.vcs.add_files')
    mocker.patch('src.vcs.commit')

    def run_command_side_effect(*args, **kwargs):
        command = args[0]
        if command[0] == "age-keygen" and "-y" in command:
            return mocker.Mock(stdout="age1testpublickey")
        return mocker.Mock(stdout="", stderr="")
        
    mock_run_command.side_effect = run_command_side_effect
    
    result = initializer.run_initialization()
    
    assert result is True
    assert os.path.isdir("/config/keys")
    
    with open("/config/.env", "r") as f:
        content = f.read()
        assert 'MASTER_AGE_KEY_STORAGE_PATH="config/keys/age-key.txt"' in content
        assert 'AGE_RECIPIENT="age1testpublickey"' in content
        
    vcs.add_files.assert_called_once()
    vcs.commit.assert_called_once()

# --- ВИПРАВЛЕННЯ ТУТ ---
# ВИПРАВЛЕНО: Додаємо фікстуру `fs` до параметрів, щоб мати доступ до файлової системи.
def test_initialization_fails_if_already_initialized(mocker, setup_fs, fs):
    """Тестує, що ініціалізація не проходить, якщо /config/.env вже існує."""
    # ВИПРАВЛЕНО: Використовуємо об'єкт `fs` для створення файлу.
    fs.create_file("/config/.env")
    mock_echo_error = mocker.patch('src.ui.echo_error')
    
    result = initializer.run_initialization()
    
    assert result is False
    mock_echo_error.assert_called_with("Repository already initialized (found /config/.env).")