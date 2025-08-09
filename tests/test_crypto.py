import os
from secure_repo import crypto, config

# `mocker` - це потужний інструмент з `pytest-mock`
def test_encrypt_unencrypted_files(mocker):
    """
    Тест перевіряє, що функція знаходить правильний файл,
    викликає `age` та `shred` і повертає правильну кількість.
    """
    # 1. Налаштування Моків (Mocks)
    # Імітуємо системні виклики, щоб не виконувати реальні команди
    mock_run = mocker.patch('secure_repo.system.run_command', return_value=True)
    
    # Імітуємо, що AGE_RECIPIENT встановлено
    mocker.patch.object(config, 'AGE_RECIPIENT', 'age1testrecipient')
    
    # Імітуємо, що os.listdir знаходить один файл для шифрування
    mocker.patch('os.listdir', return_value=['note.md', 'README.md'])
    mocker.patch('os.path.exists', return_value=False) # Файл .age ще не існує
    
    # 2. Виклик функції
    count = crypto.encrypt_unencrypted_files()
    
    # 3. Перевірки (Assertions)
    # Перевіряємо, що було зашифровано 1 файл
    assert count == 1
    
    # Перевіряємо, що `age` і `shred` були викликані з правильними аргументами
    # Створюємо очікувані виклики
    expected_age_call = mocker.call(["age", "-r", "age1testrecipient", "-o", "note.md.age", "note.md"])
    expected_shred_call = mocker.call(["shred", "-u", "note.md"])
    
    # Перевіряємо, чи були ці виклики серед усіх викликів mock_run
    mock_run.assert_has_calls([expected_age_call, expected_shred_call], any_order=True)