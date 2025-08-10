import os
import tempfile
import shutil
from . import ui, system, config

def _get_identity_file():
    """
    Отримує шлях до файлу з приватним ключем.
    Якщо ключ зашифровано GPG, розшифровує його у тимчасовий файл.
    Повертає шлях до готового для використання файлу ключа та об'єкт тимчасового файлу (для очищення).
    """
    if not config.MASTER_KEY_PATH or not os.path.exists(config.MASTER_KEY_PATH):
        ui.echo_error(f"Master key file not found at: {config.MASTER_KEY_PATH}")
        ui.echo_info("Please check the MASTER_AGE_KEY_STORAGE_PATH in your .env file.")
        return None, None

    if config.MASTER_KEY_PATH.endswith(".gpg"):
        ui.echo_info("Master key is GPG encrypted. Decrypting...")
        ui.echo_warning("You may need to enter your GPG passphrase.")
        
        # Створюємо тимчасовий файл, який буде автоматично видалено при закритті
        temp_key_file = tempfile.NamedTemporaryFile(mode='w+', delete=True)
        
        gpg_cmd = ["gpg", "--decrypt", "-o", temp_key_file.name, config.MASTER_KEY_PATH]
        if system.run_command(gpg_cmd):
            # Встановлюємо жорсткі права на тимчасовий файл
            os.chmod(temp_key_file.name, 0o600)
            return temp_key_file.name, temp_key_file
        else:
            ui.echo_error("Failed to decrypt GPG key.")
            temp_key_file.close() # Закриваємо (і видаляємо) файл
            return None, None
    else:
        # Ключ не зашифровано, просто повертаємо шлях
        return config.MASTER_KEY_PATH, None

def run_decryption():
    """
    Основний сценарій розшифровки файлів.
    """
    if not shutil.which("fzf"):
        ui.echo_error("'fzf' is not installed. Decryption requires fzf for file selection.")
        return

    identity_file, temp_key_handle = _get_identity_file()
    if not identity_file:
        return

    try:
        # Знаходимо всі файли для розшифровки
        age_files = [f for f in os.listdir('.') if f.endswith('.md.age')]
        if not age_files:
            ui.echo_info("No encrypted (.md.age) files found in this directory.")
            return

        # Готуємо команду fzf з прев'ю
        preview_command = f"age -d -i '{identity_file}' -o /dev/stdout {{}} 2>/dev/null | head -n 30"
        fzf_command = [
            "fzf", "--multi", "--height=40%", "--border",
            "--prompt=Select files to decrypt (Tab to select) > ",
            f"--preview={preview_command}"
        ]
        
        # Передаємо список файлів у fzf через stdin
        files_input = "\n".join(age_files)
        result = system.run_command(fzf_command, capture=True, stdin_input=files_input)

        if not result or not result.stdout:
            ui.echo_info("No files selected. Aborting.")
            return

        selected_files = result.stdout.strip().split('\n')
        decrypted_files = []

        ui.echo_step("Decrypting selected files...")
        for encrypted_file in selected_files:
            decrypted_file = encrypted_file.replace('.age', '')
            
            if os.path.exists(decrypted_file):
                if not ui.prompt_yes_no(f"File '{decrypted_file}' already exists. Overwrite?"):
                    ui.echo_info(f"Skipping {encrypted_file}...")
                    continue

            age_cmd = ["age", "-d", "-i", identity_file, "-o", decrypted_file, encrypted_file]
            if system.run_command(age_cmd):
                ui.echo_success(f"Successfully decrypted {encrypted_file} -> {decrypted_file}")
                decrypted_files.append(decrypted_file)
            else:
                ui.echo_error(f"Failed to decrypt {encrypted_file}.")

        if decrypted_files and config.EDITOR:
            if ui.prompt_yes_no(f"Open {len(decrypted_files)} decrypted file(s) in '{config.EDITOR}'?"):
                system.run_command([config.EDITOR] + decrypted_files)

    finally:
        # Гарантоване очищення: закриваємо (і видаляємо) тимчасовий файл ключа
        if temp_key_handle:
            ui.echo_info("Cleaning up temporary key file...")
            temp_key_handle.close()