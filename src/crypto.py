import os
from . import ui, system, config

ENCRYPTABLE_EXTENSIONS = ('.md', '.txt', '.doc', '.docx', '.rtf')
VAULT_DIR = "vault"

def encrypt_unencrypted_files():
    """Encrypts all found files with specified extensions in vault/ and removes the originals."""
    if not config.AGE_RECIPIENT:
        ui.echo_error("AGE_RECIPIENT is not set in .env file.")
        return 0
        
    if not os.path.isdir(config.VAULT_DIR):
        ui.echo_info(f"Directory '{config.VAULT_DIR}' not found. Nothing to encrypt.")
        return 0

    files_to_encrypt = [f for f in os.listdir(config.VAULT_DIR) if f.endswith(ENCRYPTABLE_EXTENSIONS)]
    encrypted_count = 0

    for filename in files_to_encrypt:
        source_path = os.path.join(config.VAULT_DIR, filename)
        encrypted_path = f"{source_path}.age"
        
        if os.path.exists(encrypted_path) and os.path.getmtime(source_path) < os.path.getmtime(encrypted_path):
            continue

        ui.echo_info(f"Encrypting {source_path}...")
        
        age_cmd = ["age", "-r", config.AGE_RECIPIENT, "-o", encrypted_path, source_path]
        if system.run_command(age_cmd):
            try:
                # Використовуємо надійний вбудований метод Python для видалення
                os.remove(source_path)
                encrypted_count += 1
            except OSError as e:
                ui.echo_error(f"Failed to delete original file {source_path}: {e}")
                ui.echo_warning(f"Encrypted file '{encrypted_path}' was created, but original was not deleted.")
    return encrypted_count