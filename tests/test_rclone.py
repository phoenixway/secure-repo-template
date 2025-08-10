from src import rclone, config, decryptor
import os

def test_run_restore_success(mocker, setup_fs):
    """
    Тестує успішний сценарій відновлення з бекапу.
    """
    # 1. Налаштування моків
    mocker.patch('shutil.which', return_value=True) # Імітуємо, що rclone є
    mocker.patch('src.config.get_config', return_value=["gdrive:backup"])
    # Імітуємо, що _get_identity_file успішно повернув ключ
    mocker.patch('src.decryptor._get_identity_file', return_value=("/fake/key.txt", None))

    mock_run_command = mocker.patch('src.system.run_command')
    
    # Налаштовуємо поведінку mock_run_command для різних етапів
    def run_command_side_effect(*args, **kwargs):
        command = args[0]
        # Коли rclone шукає файли, повертаємо список
        if command[0] == 'rclone' and command[1] == 'lsf':
            return mocker.Mock(stdout="backup1.tar.gz.age\nbackup2.tar.gz.age")
        # Коли fzf вибирає файл, повертаємо один обраний
        if command[0] == 'fzf':
            return mocker.Mock(stdout="backup2.tar.gz.age")
        # Для всіх інших команд (rclone copy, age, tar) просто повертаємо успіх
        return True

    mock_run_command.side_effect = run_command_side_effect
    mocker.patch('os.makedirs')

    # 2. Виклик функції
    rclone.run_restore()

    # 3. Перевірки
    # Перевіряємо, що rclone викликався для завантаження саме обраного файлу
    download_call = mock_run_command.call_args_list[2].args[0]
    assert download_call[0] == 'rclone'
    assert 'gdrive:backup/backup2.tar.gz.age' == download_call[2]
    
    # Перевіряємо, що age викликався для розшифровки
    decrypt_call = mock_run_command.call_args_list[3].args[0]
    assert decrypt_call[0] == 'age'

    # Перевіряємо, що tar викликався для розпаковки у правильну папку
    extract_call = mock_run_command.call_args_list[4].args[0]
    assert extract_call[0] == 'tar'
    assert extract_call[4].startswith('restored_backup_') # Перевіряємо назву папки

def test_restore_aborts_if_rclone_missing(mocker, setup_fs):
    """
    Тестує, що відновлення переривається, якщо rclone не встановлено.
    """
    mocker.patch('shutil.which', return_value=False) # rclone НЕ знайдено
    mock_echo_error = mocker.patch('src.ui.echo_error')
    mock_run_command = mocker.patch('src.system.run_command')

    rclone.run_restore()

    # Перевіряємо, що було виведено помилку і жодних команд не було виконано
    mock_echo_error.assert_called_with("'rclone' is not installed. Cannot restore from cloud.")
    assert not mock_run_command.called