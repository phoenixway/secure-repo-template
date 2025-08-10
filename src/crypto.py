import os
from . import ui, system, config

ENCRYPTABLE_EXTENSIONS = ('.md', '.txt', '.doc', '.docx', '.rtf')

def encrypt_unencrypted_files():
    """Encrypts all found files with specified extensions in vault/ and removes the originals."""
    # ОНОВЛЕНО: Використовуємо функцію для отримання конфігурації
    age_recipient = config.get_config("AGE_RECIPIENT")
    if not age_recipient:
        ui.echo_error("AGE_RECIPIENT is not set in .env file.")
        return 0
    
    # ОНОВЛЕНО: Використовуємо функцію для отримання шляху
    vault_dir = config.get_vault_dir()
    if not os.path.isdir(vault_dir):
        ui.echo_info(f"Directory '{vault_dir}' not found. Nothing to encrypt.")
        return 0

    files_to_encrypt = [f for f in os.listdir(vault_dir) if f.endswith(ENCRYPTABLE_EXTENSIONS)]
    encrypted_count = 0

    for filename in files_to_encrypt:
        source_path = os.path.join(vault_dir, filename)
        encrypted_path = f"{source_path}.age"
        
        if os.path.exists(encrypted_path) and os.path.getmtime(source_path) < os.path.getmtime(encrypted_path):
            continue

        ui.echo_info(f"Encrypting {source_path}...")
        
        age_cmd = ["age", "-r", age_recipient, "-o", encrypted_path, source_path]
        if system.run_command(age_cmd):
            try:
                os.remove(source_path)
                encrypted_count += 1
            except OSError as e:
                ui.echo_error(f"Failed to delete original file {source_path}: {e}")
                ui.echo_warning(f"Encrypted file '{encrypted_path}' was created, but original was not deleted.")
    return encrypted_count