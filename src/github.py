import os
import click
import shutil
from . import ui, system, config
# ОНОВЛЕНО: Додаємо імпорт самого себе для надійного мокінгу
import src.github as github

SSH_KEY_NAME = "github_deploy_key"
# ОНОВЛЕНО: Використовуємо функцію, а не константу, для шляху
def get_ssh_key_path():
    return os.path.join(config.get_keys_dir(), SSH_KEY_NAME)

def check_gh_auth():
    """Checks if the user is logged into the gh CLI."""
    ui.echo_info("Checking GitHub CLI authentication status...")
    if system.run_command(["gh", "auth", "status"]):
        ui.echo_success("Authenticated with GitHub CLI.")
        return True
    
    ui.echo_error("You are not logged in to the GitHub CLI.")
    ui.echo_step("Please perform these two steps in your terminal:")
    ui.echo_warning("  1. gh auth login")
    ui.echo_warning("  2. ./manager.py providers github setup")
    return False

def create_ssh_key():
    """Creates a new SSH key specifically for this repository."""
    ssh_key_path = get_ssh_key_path()
    if os.path.exists(ssh_key_path):
        ui.echo_info(f"SSH key already exists at {ssh_key_path}. Skipping creation.")
        return True
        
    ui.echo_info(f"Creating a new unique SSH deploy key in '{config.get_keys_dir()}'...")
    cmd = ["ssh-keygen", "-t", "ed25519", "-f", ssh_key_path, "-N", ""]
    if system.run_command(cmd, capture=True):
        ui.echo_success("SSH deploy key created.")
        return True
    return False

def create_repo(repo_name):
    """Creates a new private GitHub repository."""
    ui.echo_info(f"Creating new private GitHub repository: {repo_name}")
    cmd = ["gh", "repo", "create", repo_name, "--private", "-y"]
    result = system.run_command(cmd, capture=True)
    if result:
        ui.echo_success("GitHub repository created successfully.")
        return repo_name
    return None

def add_deploy_key(repo_full_name):
    """Adds the public SSH key as a deploy key to the repository."""
    ui.echo_info("Adding SSH key as a deploy key to the repository...")
    public_key_path = f"{get_ssh_key_path()}.pub"
    if not os.path.exists(public_key_path):
        ui.echo_error(f"Public SSH key not found at {public_key_path}")
        return False
        
    cmd = ["gh", "repo", "deploy-key", "add", public_key_path, "--allow-write", "--repo", repo_full_name]
    if system.run_command(cmd):
        ui.echo_success("Deploy key added with write permissions.")
        return True
    return False

def set_remote_url(repo_full_name):
    """Sets the git remote 'origin' to use the new SSH key."""
    ui.echo_info("Setting git remote 'origin'...")
    ssh_url = f"git@github.com:{repo_full_name}.git"
    
    system.run_command(["git", "remote", "remove", "origin"], capture=True)
    
    if system.run_command(["git", "remote", "add", "origin", ssh_url]):
        ui.echo_success(f"Remote 'origin' set to: {ssh_url}")
        return True
    return False

def full_setup_flow():
    """Orchestrates the entire GitHub setup process."""
    # ОНОВЛЕНО: Використовуємо префікс `github.`
    if not github.check_gh_auth():
        return
        
    repo_name = click.prompt("Please enter a name for your new GitHub repository (e.g., my-secret-notes)")

    ui.echo_step("1/4: Creating a unique SSH key...")
    if not github.create_ssh_key(): return

    ui.echo_step(f"2/4: Creating GitHub repository '{repo_name}'...")
    repo_full_name = github.create_repo(repo_name)
    if not repo_full_name: return

    ui.echo_step("3/4: Adding the SSH key as a deploy key...")
    if not github.add_deploy_key(repo_full_name): return

    ui.echo_step("4/4: Linking local repository to GitHub...")
    if not github.set_remote_url(repo_full_name): return
        
    ui.echo_success("\nGitHub setup complete!")
    ui.echo_info("You can now use './manager.py push git' to sync your encrypted files.")