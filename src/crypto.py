import os
from . import ui, system, config

# src/crypto.py
def encrypt_unencrypted_files():
    """Encrypts all found .md files in vault/ and shreds the originals."""
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
        # Перевіряємо, що шифрування пройшло успішно
        if system.run_command(age_cmd):
            # ВИПРАВЛЕНО: Тепер ми перевіряємо, що і shred спрацював
            shred_cmd = ["shred", "-u", source_path]
            if system.run_command(shred_cmd):
                encrypted_count += 1
            else:
                ui.echo_error(f"Failed to shred original file: {source_path}")
                ui.echo_warning(f"Encrypted file '{encrypted_path}' was created, but original was not deleted.")

    return encrypted_count