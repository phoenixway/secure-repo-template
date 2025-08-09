# secure_repo/initializer.py
import os
import shutil
import re
from . import ui, system, vcs

def run_initialization():
    """
    Runs the full initialization process for a new secure repository.
    This functionality is a Python port of the original init-secure-repo.sh script.
    """
    # --- Крок 1: Перевірки ---
    ui.echo_step("1/5: Running pre-flight checks...")
    if os.path.exists('.env'):
        ui.echo_error("Repository already initialized (found .env file).")
        ui.echo_info("If you want to start over, please delete the .env and age-key.txt* files.")
        return False

    if not os.path.exists('.env.example'):
        ui.echo_error(".env.example template not found. Cannot continue.")
        return False

    if not system.check_dependencies():
        ui.echo_error("Some dependencies are missing. Please install them and try again.")
        return False

    # --- Крок 2: Генерація ключа Age ---
    ui.echo_step("2/5: Generating new age private key...")
    key_file = "age-key.txt"
    if not system.run_command(["age-keygen", "-o", key_file]):
        ui.echo_error("Failed to generate age key.")
        return False
    
    ui.echo_success(f"Key successfully generated in: {key_file}")
    ui.echo_warning(f"IMPORTANT: The file '{key_file}' contains your secret key! It is ignored by Git, but you must store it securely.")

    master_key_path = key_file
    is_gpg_encrypted = False

    # --- Крок 3: Опціональне шифрування ключа GPG ---
    ui.echo_step("3/5: Securing the private key (optional GPG)...")
    if shutil.which("gpg"):
        if ui.prompt_yes_no("Do you want to encrypt the private key file with GPG for extra security?"):
            gpg_key_file = f"{key_file}.gpg"
            ui.echo_info(f"Encrypting '{key_file}' -> '{gpg_key_file}'...")
            ui.echo_warning("Please enter a strong GPG passphrase.")
            
            gpg_cmd = [
                "gpg", "--quiet", "--batch", "--yes", 
                "--symmetric", "--cipher-algo", "AES256",
                "-o", gpg_key_file, key_file
            ]
            if system.run_command(gpg_cmd):
                ui.echo_success(f"Successfully encrypted key to '{gpg_key_file}'.")
                ui.echo_info("Shredding the original unencrypted key...")
                system.run_command(["shred", "-u", key_file])
                master_key_path = gpg_key_file
                is_gpg_encrypted = True
            else:
                ui.echo_error("GPG encryption failed. The unencrypted key file has been left untouched.")
    else:
        ui.echo_warning("GPG command not found, skipping encryption step.")

    # --- Крок 4: Створення та налаштування .env ---
    ui.echo_step("4/5: Creating and configuring .env file...")
    # Отримуємо публічний ключ
    public_key = None
    if is_gpg_encrypted:
        ui.echo_info("Extracting public key from GPG-encrypted file...")
        ui.echo_warning("You may need to enter your GPG passphrase again.")
        # Використовуємо shell=True через pipe '|'
        cmd = f"gpg --decrypt '{master_key_path}' | age-keygen -y -"
        result = system.run_command([cmd], capture=True, shell=True)
        if result:
            public_key = result.stdout.strip()
    else:
        result = system.run_command(["age-keygen", "-y", master_key_path], capture=True)
        if result:
            public_key = result.stdout.strip()

    if not public_key:
        ui.echo_error("FATAL: Could not retrieve the public key. Cannot configure .env.")
        return False
        
    ui.echo_success(f"Your public key (recipient): {public_key}")
    
    # Копіюємо та модифікуємо .env
    shutil.copy('.env.example', '.env')
    
    with open('.env', 'r') as f:
        content = f.read()
    
    # Замінюємо значення за допомогою регулярних виразів
    content = re.sub(r'^(MASTER_AGE_KEY_STORAGE_PATH=).*', f'\\1"{master_key_path}"', content, flags=re.MULTILINE)
    content = re.sub(r'^(AGE_RECIPIENT=).*', f'\\1"{public_key}"', content, flags=re.MULTILINE)
    
    with open('.env', 'w') as f:
        f.write(content)
        
    ui.echo_success(".env file created and configured.")

    # --- Крок 5: Фіналізація ---
    ui.echo_step("5/5: Finalizing setup...")
    os.makedirs("backup", exist_ok=True)
    os.makedirs("personal-scripts", exist_ok=True)
    
    # Робимо перший коміт
    if vcs.repo:
        ui.echo_info("Creating initial Git commit...")
        # Додаємо файли, які не є секретами
        vcs.add_files(['.gitignore', '.env.example', 'README.md', 'manager.py', 'requirements.txt', 'secure_repo/'])
        vcs.commit("feat: Initialize secure repository")
        ui.echo_success("Initial commit created.")
    
    return True