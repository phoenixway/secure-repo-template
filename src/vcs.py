from . import ui, system, config
import git
import os
from datetime import datetime

try:
    repo = git.Repo(config.ROOT_DIR, search_parent_directories=True)
except git.InvalidGitRepositoryError:
    repo = None

def has_changes():
    """Checks if there are changes in the vault or config."""
    if not repo: return False
    # Перевіряємо зміни у файлах README, .gitignore та у папках vault/ і config/
    # `git diff` покаже і зміни, і нові файли, якщо вони додані в індекс
    staged_diff = repo.index.diff(repo.head.commit)
    unstaged_diff = repo.index.diff(None)
    untracked = repo.untracked_files
    return bool(staged_diff or unstaged_diff or untracked)


def add():
    """Adds all relevant files from vault/ to the Git index."""
    if not repo: return
    # Додаємо всі файли .md.age з vault, а також README.md
    files_to_add = [os.path.join(config.VAULT_DIR, f) for f in os.listdir(config.VAULT_DIR) if f.endswith('.md.age')]
    files_to_add.append('README.md')
    if files_to_add:
        repo.index.add(files_to_add)
        ui.echo_info(f"Added files to index.")

def add_files(files_to_add: list):
    """Adds a specific list of files and directories to the Git index."""
    if not repo: return
    try:
        repo.index.add(files_to_add)
        ui.echo_info(f"Added {len(files_to_add)} item(s) to index.")
    except git.GitCommandError as e:
        ui.echo_error(f"Failed to add files to Git: {e}")

def commit(message):
    """Commits staged changes with a timestamp."""
    if not repo: return
    full_message = f"{message} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    repo.index.commit(full_message)

def push():
    """Pushes changes to the remote 'origin'."""
    if not repo: return
    if 'origin' in repo.remotes:
        try:
            repo.remotes.origin.push()
        except git.GitCommandError as e:
            ui.echo_error(f"Failed to push to remote 'origin': {e.stderr}")
    else:
        ui.echo_warning("Remote 'origin' not configured. Skipping push.")