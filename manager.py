#!/usr/bin/env python3
import click
from src import (
    ui, crypto, vcs, cloud, system, initializer, decryptor, github, rclone
)

# --- Головна група команд ---
@click.group()
def cli():
    """Менеджер для безпечних, зашифрованих сховищ."""
    pass

# --- ДІЯ: init ---
@cli.group(help="Ініціалізація нового сховища (локального або хмарного).")
def init():
    """Initializes a new vault (local or cloud)."""
    pass

@init.group(name="local", help="Створює нову структуру сховища на вашому комп'ютері.")
def init_local():
    """Creates a new local vault structure."""
    pass

@init_local.command(name="git", help="Для текстових файлів з контролем версій.")
def init_local_git():
    """Initializes a vault for version-controlled text files (Git-based)."""
    if initializer.run_git_initialization():
        ui.echo_success("\nLocal Git-based vault initialized successfully!")
        ui.echo_info("Next step: Create a remote repository with './manager.py init cloud github'")
    else:
        ui.echo_error("\nInitialization failed.")

@init_local.command(name="archive", help="Для універсального архівного сховища.")
def init_local_archive():
    """Initializes a simple vault for universal archive backups (non-Git)."""
    if initializer.run_archive_initialization():
        ui.echo_success("\nLocal archive-based vault initialized successfully!")
        ui.echo_info("Next step: Place files in 'vault/' and run './manager.py push cloud rclone'.")
    else:
        ui.echo_error("\nInitialization failed.")

@init.group(name="cloud", help="Створює нове пусте сховище у хмарного провайдера.")
def init_cloud():
    """Creates a new empty vault on a cloud provider."""
    pass

@init_cloud.command(name="github", help="Створює новий приватний репозиторій на GitHub.")
def init_cloud_github():
    """Creates a new private GitHub repo and configures it with a unique deploy key."""
    github.full_setup_flow()

# --- ДІЯ: push ---
@cli.group(help="Відправляє зашифровані дані у хмарне сховище.")
def push():
    """Pushes encrypted data to a cloud provider."""
    pass

@push.group(name="cloud", help="Виберіть хмарного провайдера.")
def push_cloud():
    pass

@push_cloud.command(name="github", help="Робить 'git push' до віддаленого репозиторію.")
def push_cloud_github():
    """Pushes committed changes to the 'origin' remote."""
    ui.echo_info("Pushing changes to remote Git repository...")
    vcs.push()
    ui.echo_success("Push to 'github' completed.")

@push_cloud.command(name="rclone", help="Створює та завантажує універсальний архів.")
def push_cloud_rclone():
    """Creates and uploads a universal archive to configured rclone remotes."""
    ui.echo_info("Creating and uploading universal archive to cloud storage...")
    cloud.create_and_upload_archive()
    ui.echo_success("Push to 'rclone' completed.")

# --- ДІЯ: restore ---
@cli.group(help="Відновлює дані з хмарного сховища.")
def restore():
    """Restores data from a cloud provider."""
    pass

@restore.group(name="cloud", help="Виберіть хмарного провайдера.")
def restore_cloud():
    pass

@restore_cloud.command(name="github", help="Клонує існуючий репозиторій з GitHub та налаштовує його.")
def restore_cloud_github():
    """Clones an existing repository from GitHub and sets it up for use."""
    github.clone_and_setup_flow()

@restore_cloud.command(name="rclone", help="Відновлює дані з універсального хмарного архіву.")
def restore_cloud_rclone():
    """Restores data from a universal cloud archive via rclone."""
    if ui.prompt_yes_no("This will download and extract a backup into a new directory. Are you sure?"):
        rclone.run_restore()

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

@cli.command(help="Перевіряє наявність системних залежностей.")
def check_deps():
    """Checks for required system dependencies."""
    ui.echo_info("Checking dependencies...")
    system.check_dependencies()

if __name__ == '__main__':
    cli()