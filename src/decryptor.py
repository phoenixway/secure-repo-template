import os
import tempfile
import shutil
from . import ui, system, config

def _get_identity_file():
    """Gets the path to the age key, decrypting it if necessary."""
    # ОНОВЛЕНО: Використовуємо функцію для отримання конфігурації
    master_key_path = config.get_config("MASTER_KEY_PATH")

    if not master_key_path or not os.path.exists(master_key_path):
        ui.echo_error(f"Master key file not found at: {master_key_path}")
        return None, None

    if master_key_path.endswith(".gpg"):
        ui.echo_info("Master key is GPG encrypted. Decrypting...")
        temp_key_file = tempfile.NamedTemporaryFile(mode='w+', delete=True)
        gpg_cmd = ["gpg", "--decrypt", "-o", temp_key_file.name, master_key_path]
        if system.run_command(gpg_cmd):
            os.chmod(temp_key_file.name, 0o600)
            return temp_key_file.name, temp_key_file
        else:
            temp_key_file.close()
            return None, None
    else:
        return master_key_path, None

def run_decryption():
    """Main decryption script, works with the vault/ directory."""
    if not shutil.which("fzf"):
        ui.echo_error("'fzf' is not installed.")
        return

    identity_file, temp_key_handle = _get_identity_file()
    if not identity_file:
        return

    try:
        # ОНОВЛЕНО: Використовуємо функцію для отримання шляху
        vault_dir = config.get_vault_dir()
        if not os.path.isdir(vault_dir):
            ui.echo_info(f"Directory '{vault_dir}' not found.")
            return

        age_files = [f for f in os.listdir(vault_dir) if f.endswith('.md.age')]
        if not age_files:
            ui.echo_info(f"No encrypted files found in '{vault_dir}'.")
            return
        
        preview_command = f"age -d -i '{identity_file}' -o /dev/stdout {vault_dir}/{{}} 2>/dev/null | head -n 30"
        fzf_command = ["fzf", "--multi", f"--preview={preview_command}"]
        
        files_input = "\n".join(age_files)
        result = system.run_command(fzf_command, capture=True, stdin_input=files_input)

        if not result or not result.stdout:
            ui.echo_info("No files selected.")
            return

        selected_filenames = result.stdout.strip().split('\n')
        decrypted_files = []

        ui.echo_step("Decrypting selected files...")
        for filename in selected_filenames:
            encrypted_file = os.path.join(vault_dir, filename)
            decrypted_file = encrypted_file.replace('.age', '')
            
            if os.path.exists(decrypted_file) and not ui.prompt_yes_no(f"Overwrite '{decrypted_file}'?"):
                continue

            age_cmd = ["age", "-d", "-i", identity_file, "-o", decrypted_file, encrypted_file]
            if system.run_command(age_cmd):
                ui.echo_success(f"Decrypted -> {decrypted_file}")
                decrypted_files.append(decrypted_file)

        editor = config.get_config("EDITOR")
        if decrypted_files and editor:
            if ui.prompt_yes_no(f"Open decrypted file(s) in '{editor}'?"):
                system.run_command([editor] + decrypted_files)
    finally:
        if temp_key_handle:
            ui.echo_info("Cleaning up temporary key file...")
            temp_key_handle.close()