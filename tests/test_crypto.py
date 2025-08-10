from src import crypto, config
import os

def test_encrypt_new_file(mocker, setup_fs): # setup_fs тепер повертає fs
    """Тестує шифрування нового файлу у віртуальній папці /vault."""
    fs = setup_fs 
    fs.create_file("/vault/note.md", contents="secret data")
    
    mocker.patch('src.config.get_config', return_value='age1testrecipient')
    mock_run = mocker.patch('src.system.run_command', return_value=True)
    mock_remove = mocker.patch('os.remove')

    count = crypto.encrypt_unencrypted_files()

    assert count == 1
    mock_run.assert_called_once_with(["age", "-r", "age1testrecipient", "-o", "/vault/note.md.age", "/vault/note.md"])
    mock_remove.assert_called_once_with("/vault/note.md")

def test_skip_up_to_date_file(mocker, setup_fs):
    fs = setup_fs
    fs.create_file("/vault/note.md")
    fs.create_file("/vault/note.md.age")
    os.utime("/vault/note.md", (os.path.getmtime("/vault/note.md.age") - 100, os.path.getmtime("/vault/note.md.age") - 100))

    mocker.patch('src.config.get_config', return_value='age1testrecipient')
    mock_run = mocker.patch('src.system.run_command')
    mock_remove = mocker.patch('os.remove')

    count = crypto.encrypt_unencrypted_files()
    
    assert count == 0
    mock_run.assert_not_called()
    mock_remove.assert_not_called()