from src import cloud, config
import tarfile

def test_create_and_upload_archive_success(mocker, setup_fs):
    """
    Тестує успішний сценарій створення та завантаження архіву.
    """
    mocker.patch('src.config.get_config', side_effect=lambda key: {
        "CLOUD_REMOTES": ["gdrive:backup", "dropbox:backup"],
        "AGE_RECIPIENT": "age1testrecipient"
    }.get(key))
    
    mocker.patch('tarfile.open')
    mock_run_command = mocker.patch('src.system.run_command', return_value=True)
    mocker.patch('os.remove')

    cloud.create_and_upload_archive()

    # Перевіряємо, що age викликався
    age_call = mock_run_command.call_args_list[0]
    assert age_call.args[0][0] == "age"

    # Перевіряємо виклики rclone
    rclone_call_1 = mock_run_command.call_args_list[1]
    rclone_call_2 = mock_run_command.call_args_list[2]
    
    assert rclone_call_1.args[0][0] == "rclone"
    # ВИПРАВЛЕНО: Перевіряємо правильний індекс (3) для destination
    assert rclone_call_1.args[0][3] == "gdrive:backup"
    
    assert rclone_call_2.args[0][0] == "rclone"
    assert rclone_call_2.args[0][3] == "dropbox:backup"

def test_backup_skips_if_no_remotes(mocker, setup_fs):
    """
    Тестує, що бекап пропускається, якщо не налаштовано CLOUD_REMOTES.
    """
    mocker.patch('src.config.get_config', return_value=[])
    mock_echo_info = mocker.patch('src.ui.echo_info')
    mocker.patch('tarfile.open')

    cloud.create_and_upload_archive()

    # ВИПРАВЛЕНО: Текст повідомлення тепер відповідає коду
    mock_echo_info.assert_called_with("CLOUD_REMOTES not configured in .env. Skipping cloud backup.")
    assert not tarfile.open.called