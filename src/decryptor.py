import os
import tempfile
import shutil
from . import ui, system, config

def _get_identity_file():
    """Gets the path to the age key, decrypting it if necessary."""
    if not config.MASTER_KEY_PATH or not os.path.exists(config.MASTER_KEY_PATH):
        ui.echo_error(f"Master key file not found at: {config.MASTER_KEY_PATH}")
        return None, None

    if config.MASTER_KEY_PATH.endswith(".gpg"):
        ui.echo_info("Master key is GPG encrypted. Decrypting...")
        temp_key_file = tempfile.NamedTemporaryFile(mode='w+', delete=True)
        gpg_cmd = ["gpg", "--decrypt", "-o", temp_key_file.name, config.MASTER_KEY_PATH]
        if system.run_command(gpg_cmd):
            os.chmod(temp_key_file.name, 0o600)
            return temp_key_file.name, temp_key_file
        else:
            temp_key_file.close()
            return None, None
    else:
        return config.MASTER_KEY_PATH, None

def run_decryption():
    """Main decryption script, works with the vault/ directory."""
    if not shutil.which("fzf"):
        ui.echo_error("'fzf' is not installed.")
        return

    identity_file, temp_key_handle = _get_identity_file()
    if not identity_file:
        return

    try:
        if not os.path.isdir(config.VAULT_DIR):
            ui.echo_info(f"Directory '{config.VAULT_DIR}' not found.")
            return

        age_files = [f for f in os.listdir(config.VAULT_DIR) if f.endswith('.md.age')]
        if not age_files:
            ui.echo_info(f"No encrypted (.md.age) files found in '{config.VAULT_DIR}'.")
            return
        
        preview_command = f"age -d -i '{identity_file}' -o /dev/stdout {config.VAULT_DIR}/{{}} 2>/dev/null | head -n 30"
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
            encrypted_file = os.path.join(config.VAULT_DIR, filename)
            decrypted_file = encrypted_file.replace('.age', '')
            
            if os.path.exists(decrypted_file) and not ui.prompt_yes_no(f"Overwrite '{decrypted_file}'?"):
                continue

            age_cmd = ["age", "-d", "-i", identity_file, "-o", decrypted_file, encrypted_file]
            if system.run_command(age_cmd):
                ui.echo_success(f"Decrypted -> {decrypted_file}")
                decrypted_files.append(decrypted_file)

        if decrypted_files and config.EDITOR:
            if ui.prompt_yes_no(f"Open decrypted file(s) in '{config.EDITOR}'?"):
                system.run_command([config.EDITOR] + decrypted_files)
    finally:
        if temp_key_handle:
            ui.echo_info("Cleaning up temporary key file...")
            temp_key_handle.close()