import click
# Додаємо decryptor до імпортів
from secure_repo import ui, crypto, vcs, cloud, system, initializer, decryptor

@click.group()
def cli():
    """A CLI tool for managing a secure, encrypted repository."""
    pass

# ... (команди init, check_deps, encrypt, push залишаються без змін) ...
@cli.command()
def init():
    # ...
    if initializer.run_initialization():
        ui.echo_success("\nInitialization complete! Your secure repository is ready.")
        ui.echo_info("Try creating a .md file and run 'python manager.py encrypt'.")
    else:
        ui.echo_error("\nInitialization failed. Please check the messages above.")

@cli.command()
def check_deps():
    # ...
    ui.echo_info("Checking dependencies...")
    system.check_dependencies()

@cli.command()
def encrypt():
    # ...
    ui.echo_step("1/2: Encrypting local files...")
    count = crypto.encrypt_unencrypted_files()
    if count == 0:
        ui.echo_info("No new or modified files to encrypt.")
    ui.echo_step("2/2: Committing to Git...")
    if vcs.has_changes():
        vcs.add()
        vcs.commit("chore: Update encrypted notes")
        ui.echo_success("Changes committed to Git.")
    else:
        ui.echo_info("No changes to commit.")

@cli.command()
@click.argument('target', type=click.Choice(['git', 'rclone']), required=True)
def push(target):
    # ...
    if target == 'git':
        ui.echo_info("Pushing changes to remote Git repository...")
        vcs.push()
    elif target == 'rclone':
        ui.echo_info("Creating and uploading backup to cloud storage...")
        cloud.create_and_upload_backup()
    ui.echo_success(f"Push to '{target}' completed.")


# --- НОВА КОМАНДА ---
@cli.command()
def decrypt():
    """Interactively decrypts one or more notes for editing."""
    decryptor.run_decryption()
    ui.echo_warning("\nDon't forget to run 'encrypt' again after you finish your work!")


if __name__ == '__main__':
    cli()