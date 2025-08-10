from secure_repo import decryptor, config
import os

def test_run_decryption_success(mocker, fs):
    """
    Тестує успішний сценарій розшифровки одного файлу.
    """
    # 1. Налаштування середовища та моків
    fs.create_file("note1.md.age")
    fs.create_file("secrets/key.txt")
    
    mocker.patch.object(config, 'MASTER_KEY_PATH', 'secrets/key.txt')
    # Імітуємо, що у конфігурації є редактор
    mocker.patch.object(config, 'EDITOR', '/usr/bin/nano') 
    
    mocker.patch('shutil.which', return_value=True)
    
    # --- ВИПРАВЛЕННЯ ---
    # Мокаємо prompt_yes_no, щоб уникнути інтерактивного вводу під час тесту
    mocker.patch('secure_repo.ui.prompt_yes_no', return_value=False)
    
    mock_run_command = mocker.patch('secure_repo.system.run_command')
    
    mock_fzf_result = mocker.Mock(stdout="note1.md.age\n")
    def run_command_side_effect(*args, **kwargs):
        command = args[0]
        if command[0] == 'fzf':
            return mock_fzf_result
        # Для виклику `age -d` імітуємо створення файлу
        if command[0] == 'age':
            fs.create_file("note1.md", contents="decrypted data")
            # Повертаємо Mock, а не True
            return mocker.Mock(stdout="", stderr="")
        return mocker.Mock(stdout="", stderr="")

    mock_run_command.side_effect = run_command_side_effect
    
    # 2. Викликаємо функцію
    decryptor.run_decryption()
    
    # 3. Перевіряємо результат
    assert mock_run_command.call_args_list[0].args[0][0] == 'fzf'
    assert mock_run_command.call_args_list[1].args[0][0] == 'age'
    assert os.path.exists("note1.md")


def test_decryption_aborts_if_no_files_selected(mocker, fs):
    """
    Тестує, що нічого не відбувається, якщо користувач нічого не вибрав у fzf.
    """
    fs.create_file("note1.md.age")
    fs.create_file("secrets/key.txt")
    mocker.patch.object(config, 'MASTER_KEY_PATH', 'secrets/key.txt')
    
    mocker.patch('shutil.which', return_value=True)

    mock_fzf_result = mocker.Mock(stdout="")
    mock_run_command = mocker.patch('secure_repo.system.run_command', return_value=mock_fzf_result)
    
    decryptor.run_decryption()
    
    mock_run_command.assert_called_once()
    assert mock_run_command.call_args_list[0].args[0][0] == 'fzf'