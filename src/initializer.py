import os
import shutil
import re
from . import ui, system, vcs, config

def run_git_initialization():
    """
    Runs the full initialization process for a new Git-based secure repository.
    """
    # --- Кроки 1-4 залишаються без змін ---
    ui.echo_step("1/5: Running pre-flight checks...")
    if os.path.exists(config.get_env_path()):
        ui.echo_error(f"Repository already initialized (found {config.get_env_path()}).")
        return False
    if not os.path.exists(os.path.join(config.get_config_dir(), '.env.example')):
        ui.echo_error(".env.example not found in config/ directory.")
        return False
    if not system.check_dependencies():
        ui.echo_error("Some dependencies are missing.")
        return False

    ui.echo_step("2/5: Creating directories and generating new age key...")
    os.makedirs(config.get_keys_dir(), exist_ok=True)
    os.makedirs(config.get_vault_dir(), exist_ok=True)
    key_file_path = os.path.join(config.get_keys_dir(), "age-key.txt")
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
    
    env_path = config.get_env_path()
    shutil.copy(os.path.join(config.get_config_dir(), '.env.example'), env_path)
    with open(env_path, 'r') as f: content = f.read()
    master_key_path_relative = os.path.relpath(master_key_path_abs, config.get_root_dir())
    content = re.sub(r'^(MASTER_AGE_KEY_STORAGE_PATH=).*', f'\\1"{master_key_path_relative}"', content, flags=re.MULTILINE)
    content = re.sub(r'^(AGE_RECIPIENT=).*', f'\\1"{public_key}"', content, flags=re.MULTILINE)
    with open(env_path, 'w') as f: f.write(content)
    ui.echo_success(f".env file created and configured in {config.get_config_dir()}/")

    # --- ВИПРАВЛЕННЯ: Крок 5 ---
    # Лише ініціалізуємо Git-репозиторій, не роблячи коміту.
    ui.echo_step("5/5: Finalizing setup...")
    os.makedirs("backup", exist_ok=True)
    
    if not vcs.is_git_repo():
        ui.echo_info("Initializing local Git repository...")
        vcs.init_repo()
        ui.echo_success("Local Git repository has been initialized.")
    
    return True