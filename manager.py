#!/usr/-bin/env python3
import click
from src import (
    ui, crypto, vcs, cloud, system, initializer, decryptor, github, rclone
)

# --- Головна група команд ---
@click.group()
def cli():
    """Менеджер для безпечних, зашифрованих сховищ."""
    pass

# --- Група команд `init` ---
@cli.group(help="Створює локальне сховище обраного типу.")
def init():
    """Initializes a local vault of a specified type."""
    pass

@init.command(name="git", help="Створює сховище для текстових файлів на основі Git.")
def init_git():
    """Initializes a vault for version-controlled text files (Git-based)."""
    # ОНОВЛЕНО: Викликаємо перейменовану функцію
    if initializer.run_git_initialization():
        ui.echo_success("\nLocal Git-based vault initialized successfully!")
        ui.echo_info("Next step: Connect it to a remote provider using './manager.py providers github create'")
    else:
        ui.echo_error("\nInitialization failed. Please check the messages above.")

# --- Основні щоденні команди ---
@cli.command(help="Шифрує всі нові/змінені файли у папці vault/ та робить коміт.")
def encrypt():
    """Encrypts all new/modified files in vault/ and makes a commit."""
    ui.echo_step("1/2: Encrypting local files...")
    count = crypto.encrypt_unencrypted_files()
    if count == 0:
        ui.echo_info("No new or modified files to encrypt in 'vault/'.")

    ui.echo_step("2/2: Committing to Git...")
    if vcs.has_changes():
        vcs.add()
        vcs.commit("chore: Update encrypted notes")
        ui.echo_success("Changes committed to Git.")
    else:
        ui.echo_info("No changes to commit.")

@cli.command(help="Інтерактивно розшифровує нотатки для редагування.")
def decrypt():
    """Interactively decrypts one or more notes for editing."""
    decryptor.run_decryption()
    ui.echo_warning("\nDon't forget to run 'encrypt' again after you finish your work!")

@cli.command(help="Відправляє зміни на віддалений ресурс: 'git' або 'rclone'.")
@click.argument('target', type=click.Choice(['git', 'rclone']), required=True)
def push(target):
    """Pushes changes to a remote resource: 'git' or 'rclone'."""
    if target == 'git':
        ui.echo_info("Pushing changes to remote Git repository...")
        vcs.push()
    elif target == 'rclone':
        ui.echo_info("Creating and uploading universal archive to cloud storage...")
        cloud.create_and_upload_archive()
    
    ui.echo_success(f"Push to '{target}' completed.")

@cli.command(help="Перевіряє наявність системних залежностей.")
def check_deps():
    """Checks for required system dependencies."""
    ui.echo_info("Checking dependencies...")
    system.check_dependencies()

# --- Група команд для провайдерів ---
@cli.group(help="Команди для налаштування та роботи з хмарними провайдерами.")
def providers():
    """Commands for setting up and managing cloud providers."""
    pass

# --- Підгрупа для GitHub ---
@providers.group(name="github", help="Команди для взаємодії з GitHub.")
def github_cli():
    pass

@github_cli.command(name="create", help="Створює новий приватний репозиторій на GitHub та налаштовує доступ.")
def create_github():
    """Creates a new private GitHub repo and configures it with a unique deploy key."""
    github.full_setup_flow()

@github_cli.command(name="clone", help="Клонує існуючий репозиторій з GitHub та налаштовує його.")
def clone_github():
    """Clones and sets up an existing secure repository from GitHub."""
    github.clone_and_setup_flow()

# --- Підгрупа для Rclone ---
@providers.group(name="rclone", help="Команди для взаємодії з архівами через rclone.")
def rclone_cli():
    pass

@rclone_cli.command(name="restore", help="Відновлює дані з універсального хмарного архіву.")
def restore_rclone():
    """Restores the repository from a universal cloud archive."""
    if ui.prompt_yes_no("This will download and extract a backup into a new directory. Are you sure?"):
        rclone.run_restore()

providers.add_command(github_cli)
providers.add_command(rclone_cli)

if __name__ == '__main__':
    cli()