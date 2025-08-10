import click
from src import ui, crypto, vcs, cloud, system, initializer, decryptor

@click.group()
def cli():
    """A CLI tool for managing a secure, encrypted repository."""
    pass

@cli.command()
def init():
    """Initializes the secure repository (creates keys, .env file)."""
    if initializer.run_initialization():
        ui.echo_success("\nInitialization complete! Your secure repository is ready.")
        ui.echo_info("Try creating a .md file in the 'vault/' directory and run 'python manager.py encrypt'.")
    else:
        ui.echo_error("\nInitialization failed. Please check the messages above.")

@cli.command()
def check_deps():
    """Checks for required external dependencies like age, gpg, rclone."""
    ui.echo_info("Checking dependencies...")
    system.check_dependencies()

@cli.command()
def encrypt():
    """Encrypts all unencrypted .md files in vault/ and commits them to Git."""
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

@cli.command()
def decrypt():
    """Interactively decrypts one or more notes for editing."""
    decryptor.run_decryption()
    ui.echo_warning("\nDon't forget to run 'encrypt' again after you finish your work!")

@cli.command()
@click.argument('target', type=click.Choice(['git', 'rclone']), required=True)
def push(target):
    """Pushes changes to a remote target (git or rclone)."""
    if target == 'git':
        ui.echo_info("Pushing changes to remote Git repository...")
        vcs.push()
    elif target == 'rclone':
        ui.echo_info("Creating and uploading backup to cloud storage...")
        cloud.create_and_upload_backup()
    
    ui.echo_success(f"Push to '{target}' completed.")

if __name__ == '__main__':
    cli()