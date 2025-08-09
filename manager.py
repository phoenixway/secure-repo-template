import click
from secure_repo import ui, crypto, vcs, cloud, system

@click.group()
def cli():
    """A CLI tool for managing a secure, encrypted repository."""
    pass

@cli.command()
def init():
    """Initializes the secure repository (creates keys, .env file)."""
    ui.echo_warning("Initialization function is not fully implemented yet.")
    # Тут буде логіка з scenarios/init.sh

@cli.command()
def check_deps():
    """Checks for required external dependencies like age, gpg, rclone."""
    ui.echo_info("Checking dependencies...")
    system.check_dependencies()

@cli.command()
def encrypt():
    """Encrypts all unencrypted .md files and commits them to Git."""
    ui.echo_step("1/2: Encrypting local files...")
    # Ця функціональність замінює encrypt-unencrypted.sh
    count = crypto.encrypt_unencrypted_files()
    if count == 0:
        ui.echo_info("No new or modified files to encrypt.")

    ui.echo_step("2/2: Committing to Git...")
    # Ця функціональність замінює частину логіки з encrypt-n-store.sh
    if vcs.has_changes():
        vcs.add()
        vcs.commit("chore: Update encrypted notes")
        ui.echo_success("Changes committed to Git.")
    else:
        ui.echo_info("No changes to commit.")

@cli.command()
@click.argument('target', type=click.Choice(['git', 'rclone']), required=True)
def push(target):
    """Pushes changes to a remote target (git or rclone)."""
    if target == 'git':
        # Ця функціональність замінює частину логіки з encrypt-n-store.sh
        ui.echo_info("Pushing changes to remote Git repository...")
        vcs.push()
    elif target == 'rclone':
        # Ця функціональність замінює push-to-clouds.sh
        ui.echo_info("Creating and uploading backup to cloud storage...")
        cloud.create_and_upload_backup()
    
    ui.echo_success(f"Push to '{target}' completed.")

if __name__ == '__main__':
    cli()