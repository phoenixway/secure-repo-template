from secure_repo import crypto, config
import os

# ВИПРАВЛЕНО: Використовуємо фікстуру `fs` напряму
def test_encrypt_new_file(mocker, fs):
    """
    Тестує шифрування нового файлу.
    """
    # 1. Налаштування середовища
    # Тепер `fs` - це об'єкт віртуальної файлової системи
    fs.create_file("note.md", contents="secret data")
    mocker.patch.object(config, 'AGE_RECIPIENT', 'age1testrecipient')
    mock_run = mocker.patch('secure_repo.system.run_command', return_value=True)

    # 2. Виклик функції
    count = crypto.encrypt_unencrypted_files()

    # 3. Перевірки
    assert count == 1
    expected_age_call = mocker.call(["age", "-r", "age1testrecipient", "-o", "note.md.age", "note.md"])
    expected_shred_call = mocker.call(["shred", "-u", "note.md"])
    mock_run.assert_has_calls([expected_age_call, expected_shred_call])

# ВИПРАВЛЕНО: Використовуємо фікстуру `fs` напряму
def test_skip_up_to_date_file(mocker, fs):
    """
    Тестує, що файл не перешифровується, якщо він не змінювався.
    """
    # 1. Налаштування: створюємо .md та .md.age, де .age новіший
    fs.create_file("note.md")
    fs.create_file("note.md.age")
    # Встановлюємо час модифікації: .md - 100с тому, .age - зараз
    os.utime("note.md", (os.path.getmtime("note.md.age") - 100, os.path.getmtime("note.md.age") - 100))

    mocker.patch.object(config, 'AGE_RECIPIENT', 'age1testrecipient')
    mock_run = mocker.patch('secure_repo.system.run_command')

    # 2. Виклик функції
    count = crypto.encrypt_unencrypted_files()
    
    # 3. Перевірки
    assert count == 0
    mock_run.assert_not_called()