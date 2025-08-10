import os
import shutil
import re
from . import ui, system, vcs, config

def run_initialization():
    """Runs the full initialization process using the new directory structure."""
    ui.echo_step("1/5: Running pre-flight checks...")
    if os.path.exists(config.ENV_PATH):
        ui.echo_error(f"Repository already initialized (found {config.ENV_PATH}).")
        return False
    if not os.path.exists(os.path.join(config.CONFIG_DIR, '.env.example')):
        ui.echo_error(".env.example not found in config/ directory.")
        return False
    if not system.check_dependencies():
        ui.echo_error("Some dependencies are missing. Please install them and try again.")
        return False

    ui.echo_step("2/5: Creating directories and generating new age key...")
    os.makedirs(config.KEYS_DIR, exist_ok=True)
    os.makedirs(config.VAULT_DIR, exist_ok=True)
    
    key_file_path = os.path.join(config.KEYS_DIR, "age-key.txt")
    
    if not system.run_command(["age-keygen", "-o", key_file_path]):
        return False
    
    ui.echo_success(f"Key successfully generated in: {key_file_path}")
    master_key_path_abs = key_file_path
    is_gpg_encrypted = False

    ui.echo_step("3/5: Securing the private key (optional GPG)...")
    if shutil.which("gpg"):
        if ui.prompt_yes_no("Do you want to encrypt the private key file with GPG?"):
            gpg_key_file_path = f"{key_file_path}.gpg"
            gpg_cmd = ["gpg", "--quiet", "--batch", "--yes", "--symmetric", "--cipher-algo", "AES256", "-o", gpg_key_file_path, key_file_path]
            if system.run_command(gpg_cmd):
                system.run_command(["shred", "-u", key_file_path])
                master_key_path_abs = gpg_key_file_path
                is_gpg_encrypted = True

    ui.echo_step("4/5: Creating and configuring .env file...")
    public_key = None
    if is_gpg_encrypted:
        cmd = f"gpg --decrypt '{master_key_path_abs}' | age-keygen -y -"
        result = system.run_command([cmd], capture=True, shell=True)
        if result: public_key = result.stdout.strip()
    else:
        result = system.run_command(["age-keygen", "-y", master_key_path_abs], capture=True)
        if result: public_key = result.stdout.strip()
    
    if not public_key:
        ui.echo_error("FATAL: Could not retrieve public key.")
        return False
    ui.echo_success(f"Your public key (recipient): {public_key}")
    
    shutil.copy(os.path.join(config.CONFIG_DIR, '.env.example'), config.ENV_PATH)
    
    with open(config.ENV_PATH, 'r') as f: content = f.read()
    
    # Записуємо відносний шлях у .env
    master_key_path_relative = os.path.relpath(master_key_path_abs, config.ROOT_DIR)
    content = re.sub(r'^(MASTER_AGE_KEY_STORAGE_PATH=).*', f'\\1"{master_key_path_relative}"', content, flags=re.MULTILINE)
    content = re.sub(r'^(AGE_RECIPIENT=).*', f'\\1"{public_key}"', content, flags=re.MULTILINE)
    
    with open(config.ENV_PATH, 'w') as f: f.write(content)
    ui.echo_success(f".env file created and configured in {config.CONFIG_DIR}/")

    ui.echo_step("5/5: Finalizing setup...")
    os.makedirs("backup", exist_ok=True)
    
    if vcs.repo:
        ui.echo_info("Creating initial Git commit...")
        # Додаємо всі основні файли
        vcs.add_files(['.gitignore', 'config/.env.example', 'README.md', 'manager.py', 'requirements.txt', 'src/'])
        vcs.commit("feat: Initialize secure repository structure")
        ui.echo_success("Initial commit created.")
    
    return True