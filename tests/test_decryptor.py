from src import decryptor, config
import os

def test_run_decryption_success(mocker, fs):
    """
    Тестує успішний сценарій розшифровки одного файлу з папки vault/.
    """
    # 1. Налаштування середовища та моків
    # Створюємо віртуальні папки та файли згідно з новою структурою
    fs.create_dir("vault")
    fs.create_dir("config/keys")
    fs.create_file("vault/note1.md.age")
    fs.create_file("config/keys/key.txt")
    
    # Мокаємо (імітуємо) конфігурацію, щоб вона вказувала на наші фейкові файли
    mocker.patch.object(config, 'MASTER_KEY_PATH', 'config/keys/key.txt')
    mocker.patch.object(config, 'VAULT_DIR', 'vault') # Явно вказуємо папку сховища
    
    # Імітуємо, що `fzf` встановлено в системі
    mocker.patch('shutil.which', return_value=True)
    
    # Мокаємо prompt_yes_no, щоб уникнути інтерактивного вводу під час тесту
    mocker.patch('src.ui.prompt_yes_no', return_value=False)
    
    # Мокаємо функцію запуску команд
    mock_run_command = mocker.patch('src.system.run_command')
    
    # Налаштовуємо мок fzf, щоб він "повернув" обраний файл
    mock_fzf_result = mocker.Mock(stdout="note1.md.age\n")
    
    # Налаштовуємо поведінку mock_run_command для різних викликів
    def run_command_side_effect(*args, **kwargs):
        command = args[0]
        if command[0] == 'fzf':
            return mock_fzf_result
        if command[0] == 'age':
            # Імітуємо створення розшифрованого файлу
            fs.create_file("vault/note1.md", contents="decrypted data")
            return mocker.Mock(stdout="", stderr="")
        return mocker.Mock(stdout="", stderr="")

    mock_run_command.side_effect = run_command_side_effect
    
    # 2. Викликаємо функцію, яку тестуємо
    decryptor.run_decryption()
    
    # 3. Перевіряємо результат
    # Перевіряємо, що fzf був викликаний
    assert mock_run_command.call_args_list[0].args[0][0] == 'fzf'
    # Перевіряємо, що age -d був викликаний
    assert mock_run_command.call_args_list[1].args[0][0] == 'age'
    # Перевіряємо, що розшифрований файл було створено у віртуальній папці vault/
    assert os.path.exists("vault/note1.md")


def test_decryption_aborts_if_no_files_selected(mocker, fs):
    """
    Тестує, що нічого не відбувається, якщо користувач нічого не вибрав у fzf.
    """
    # 1. Налаштування середовища та моків
    fs.create_dir("vault")
    fs.create_dir("config/keys")
    fs.create_file("vault/note1.md.age")
    fs.create_file("config/keys/key.txt")
    
    mocker.patch.object(config, 'MASTER_KEY_PATH', 'config/keys/key.txt')
    mocker.patch.object(config, 'VAULT_DIR', 'vault')
    mocker.patch('shutil.which', return_value=True)

    # Мокаємо fzf, щоб він повернув порожній результат (користувач натиснув Esc)
    mock_fzf_result = mocker.Mock(stdout="")
    mock_run_command = mocker.patch('src.system.run_command', return_value=mock_fzf_result)
    
    # 2. Викликаємо функцію
    decryptor.run_decryption()
    
    # 3. Перевіряємо результат
    # Перевіряємо, що був викликаний лише fzf (1 раз)
    mock_run_command.assert_called_once()
    assert mock_run_command.call_args_list[0].args[0][0] == 'fzf'
    # Перевіряємо, що розшифрований файл НЕ було створено
    assert not os.path.exists("vault/note1.md")