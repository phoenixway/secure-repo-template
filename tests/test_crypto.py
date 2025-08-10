from src import crypto, config
import os

# ВИПРАВЛЕНО: Додаємо `fs` до параметрів, щоб мати доступ до ФС
def test_encrypt_new_file(mocker, setup_fs, fs):
    """Тестує шифрування нового файлу у віртуальній папці /vault."""
    # `setup_fs` вже виконав всю підготовку, тепер використовуємо `fs`
    fs.create_file("/vault/note.md", contents="secret data")
    
    mocker.patch.object(config, 'AGE_RECIPIENT', 'age1testrecipient')
    mock_run = mocker.patch('src.system.run_command', return_value=True)

    count = crypto.encrypt_unencrypted_files()

    assert count == 1
    expected_age_call = mocker.call(["age", "-r", "age1testrecipient", "-o", "/vault/note.md.age", "/vault/note.md"])
    expected_shred_call = mocker.call(["shred", "-u", "/vault/note.md"])
    mock_run.assert_has_calls([expected_age_call, expected_shred_call])

# ВИПРАВЛЕНО: Додаємо `fs` до параметрів
def test_skip_up_to_date_file(mocker, setup_fs, fs):
    """Тестує, що файл у /vault не перешифровується, якщо він не змінювався."""
    fs.create_file("/vault/note.md")
    fs.create_file("/vault/note.md.age")
    os.utime("/vault/note.md", (os.path.getmtime("/vault/note.md.age") - 100, os.path.getmtime("/vault/note.md.age") - 100))

    mocker.patch.object(config, 'AGE_RECIPIENT', 'age1testrecipient')
    mock_run = mocker.patch('src.system.run_command')

    count = crypto.encrypt_unencrypted_files()
    
    assert count == 0
    mock_run.assert_not_called()