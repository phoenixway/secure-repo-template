from secure_repo import initializer, ui, vcs
import os

# Цей тест вже проходить, але ми покращимо імітаційну функцію для узгодженості
def test_run_initialization_success_no_gpg(mocker, setup_fs):
    """
    Тестує успішний сценарій ініціалізації БЕЗ шифрування GPG.
    """
    mock_run_command = mocker.patch('secure_repo.system.run_command')
    mocker.patch('secure_repo.system.check_dependencies', return_value=True)
    mocker.patch('secure_repo.ui.prompt_yes_no', return_value=False)
    mocker.patch('secure_repo.vcs.add_files')
    mocker.patch('secure_repo.vcs.commit')

    def run_command_side_effect(*args, **kwargs):
        command = args[0]
        if command[0] == "age-keygen" and "-y" in command:
            return mocker.Mock(stdout="age1testpublickey")
        # Для всіх інших команд повертаємо Mock, який веде себе як успішний процес
        return mocker.Mock(stdout="", stderr="")
        
    mock_run_command.side_effect = run_command_side_effect
    
    result = initializer.run_initialization()
    
    assert result is True
    assert os.path.isdir("secrets")
    
    with open(".env", "r") as f:
        content = f.read()
        assert 'MASTER_AGE_KEY_STORAGE_PATH="secrets/age-key.txt"' in content
        assert 'AGE_RECIPIENT="age1testpublickey"' in content
        
    vcs.add_files.assert_called_once()
    vcs.commit.assert_called_once()

# ВИПРАВЛЕНО: Додаємо фікстуру `fs` до параметрів
def test_initialization_fails_if_already_initialized(mocker, setup_fs, fs):
    """
    Тестує, що ініціалізація не проходить, якщо .env вже існує.
    """
    # ВИПРАВЛЕНО: Використовуємо `fs` для створення файлу
    fs.create_file(".env")
    mock_echo_error = mocker.patch('secure_repo.ui.echo_error')
    
    result = initializer.run_initialization()
    
    assert result is False
    mock_echo_error.assert_called_with("Repository already initialized (found .env file).")

# ВИПРАВЛЕНО: Покращена логіка імітації
def test_run_initialization_success_with_gpg(mocker, setup_fs):
    """
    Тестує успішний сценарій ініціалізації З шифруванням GPG.
    """
    mock_run_command = mocker.patch('secure_repo.system.run_command')
    mocker.patch('secure_repo.system.check_dependencies', return_value=True)
    mocker.patch('secure_repo.ui.prompt_yes_no', return_value=True)
    mocker.patch('secure_repo.vcs.add_files')
    mocker.patch('secure_repo.vcs.commit')
    mocker.patch('shutil.which', return_value=True)

    def run_command_side_effect(*args, **kwargs):
        command = args[0]
        # ВИПРАВЛЕНО: Перевіряємо, що команда - це список, і шукаємо підрядок у першому елементі
        if isinstance(command, list) and len(command) == 1 and "gpg --decrypt" in command[0]:
            return mocker.Mock(stdout="age1gpgpublickey")
        
        # Для всіх інших команд повертаємо стандартний успішний результат
        return mocker.Mock(stdout="", stderr="")
        
    mock_run_command.side_effect = run_command_side_effect
    
    result = initializer.run_initialization()
    
    assert result is True
    
    with open(".env", "r") as f:
        content = f.read()
        assert 'MASTER_AGE_KEY_STORAGE_PATH="secrets/age-key.txt.gpg"' in content
        assert 'AGE_RECIPIENT="age1gpgpublickey"' in content
        
    mock_run_command.assert_any_call(["shred", "-u", "secrets/age-key.txt"])
    
    vcs.add_files.assert_called_once()
    vcs.commit.assert_called_once()