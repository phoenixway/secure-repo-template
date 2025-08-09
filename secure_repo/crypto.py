import os
from . import ui, system, config

def encrypt_unencrypted_files():
    """Encrypts all found .md files and shreds the originals."""
    if not config.AGE_RECIPIENT:
        ui.echo_error("AGE_RECIPIENT is not set in .env file.")
        return 0

    files_to_encrypt = [f for f in os.listdir('.') if f.endswith('.md') and f != "README.md"]
    encrypted_count = 0

    for filename in files_to_encrypt:
        encrypted_filename = f"{filename}.age"
        
        # Перешифровуємо, тільки якщо .md файл новіший
        if os.path.exists(encrypted_filename) and os.path.getmtime(filename) < os.path.getmtime(encrypted_filename):
            continue

        ui.echo_info(f"Encrypting {filename}...")
        
        age_cmd = ["age", "-r", config.AGE_RECIPIENT, "-o", encrypted_filename, filename]
        if system.run_command(age_cmd):
            shred_cmd = ["shred", "-u", filename]
            system.run_command(shred_cmd)
            encrypted_count += 1
            
    return encrypted_count