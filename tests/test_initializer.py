from src import initializer, vcs
import os

def test_run_git_initialization_success_no_gpg(mocker, setup_fs):
    """Тестує успішний сценарій ініціалізації БЕЗ шифрування GPG."""
    mock_run_command = mocker.patch('src.system.run_command')
    mocker.patch('src.system.check_dependencies', return_value=True)
    mocker.patch('src.ui.prompt_yes_no', return_value=False)
    # Тепер ці функції існують, і ми можемо їх мокати
    mock_init_repo = mocker.patch('src.vcs.init_repo')
    mocker.patch('src.vcs.is_git_repo', return_value=False)

    def run_command_side_effect(*args, **kwargs):
        command = args[0]
        if command[0] == "age-keygen" and "-y" in command:
            return mocker.Mock(stdout="age1testpublickey")
        return mocker.Mock(stdout="", stderr="")
        
    mock_run_command.side_effect = run_command_side_effect
    
    result = initializer.run_git_initialization()
    
    assert result is True
    assert os.path.isdir("/config/keys")
    # Перевіряємо, що `git init` був викликаний
    mock_init_repo.assert_called_once()

def test_initialization_fails_if_already_initialized(mocker, setup_fs):
    """Тестує, що ініціалізація не проходить, якщо /config/.env вже існує."""
    fs = setup_fs
    fs.create_file("/config/.env")
    mock_echo_error = mocker.patch('src.ui.echo_error')
    
    result = initializer.run_git_initialization()
    
    assert result is False
    mock_echo_error.assert_called_with("Repository already initialized (found /config/.env).")