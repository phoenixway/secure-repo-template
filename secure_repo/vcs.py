# secure_repo/vcs.py (нова версія з GitPython)
from . import ui
import git
import os
from datetime import datetime

# Ініціалізуємо об'єкт репозиторію один раз
try:
    repo = git.Repo(os.getcwd(), search_parent_directories=True)
except git.InvalidGitRepositoryError:
    repo = None # Або можна ініціалізувати новий: git.Repo.init()

def has_changes():
    """Checks if there are any changes (staged or unstaged) or untracked files."""
    if not repo: return False
    return repo.is_dirty(untracked_files=True)

def add():
    """Adds all relevant files to the Git index."""
    if not repo: return
    # Додаємо всі .md.age файли та README.md
    files_to_add = [f for f in os.listdir('.') if f.endswith('.md.age')]
    files_to_add.append('README.md')
    repo.index.add(files_to_add)
    ui.echo_info(f"Added {len(files_to_add)} file(s) to index.")

def commit(message_prefix="chore: Update encrypted notes"):
    """Commits staged changes with a timestamp."""
    if not repo: return
    timestamp = datetime.now().strftime("%Y-%м-%d %H:%M:%S")
    full_message = f"{message_prefix} at {timestamp}"
    repo.index.commit(full_message)

def push():
    """Pushes changes to the remote 'origin'."""
    if not repo: return
    if 'origin' in repo.remotes:
        try:
            repo.remotes.origin.push()
        except git.GitCommandError as e:
            ui.echo_error("Failed to push to remote 'origin'.")
            ui.echo_error(str(e))
    else:
        ui.echo_warning("Remote 'origin' not configured. Skipping push.")