from . import ui, config
import git
import os
from datetime import datetime

def _get_repo(init_if_not_found=False):
    """
    Ініціалізує (опціонально) та повертає об'єкт репозиторію,
    використовуючи динамічний шлях з конфігурації.
    """
    try:
        return git.Repo(config.get_root_dir(), search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        if init_if_not_found:
            return git.Repo.init(config.get_root_dir())
        return None

# --- НОВА ФУНКЦІЯ ---
def is_git_repo():
    """Перевіряє, чи є поточна директорія Git-репозиторієм."""
    return _get_repo() is not None

# --- НОВА ФУНКЦІЯ ---
def init_repo():
    """Ініціалізує новий Git-репозиторій у поточній директорії."""
    return _get_repo(init_if_not_found=True) is not None

def has_changes():
    """Перевіряє, чи є будь-які зміни."""
    repo = _get_repo()
    if not repo: return False
    return repo.is_dirty(untracked_files=True)

def add():
    """Додає всі релевантні файли з vault/ до індексу Git."""
    repo = _get_repo()
    if not repo: return
    
    vault_dir = config.get_vault_dir()
    root_dir = config.get_root_dir()
    
    files_to_add = []
    if os.path.isdir(vault_dir):
        # Додаємо лише зашифровані файли з vault
        files_to_add.extend([os.path.join(vault_dir, f) for f in os.listdir(vault_dir) if f.endswith(('.age'))])

    readme_path = os.path.join(root_dir, 'README.md')
    if os.path.exists(readme_path):
        files_to_add.append(readme_path)
        
    if files_to_add:
        try:
            repo.index.add(files_to_add)
            ui.echo_info("Added files to index.")
        except git.GitCommandError as e:
            ui.echo_warning(f"Could not add files to Git: {e}")

def add_files(files_to_add: list):
    """Додає конкретний список файлів та директорій до індексу Git."""
    repo = _get_repo()
    if not repo: return
    try:
        relative_paths = [os.path.relpath(p, config.get_root_dir()) for p in files_to_add]
        repo.index.add(relative_paths)
        ui.echo_info(f"Added {len(relative_paths)} item(s) to index.")
    except (git.GitCommandError, FileNotFoundError) as e:
        ui.echo_error(f"Failed to add files to Git: {e}")


def commit(message):
    """Робить коміт з таймстемпом."""
    repo = _get_repo()
    if not repo: return
    full_message = f"{message} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    repo.index.commit(full_message)

def push():
    """Робить push на 'origin'."""
    repo = _get_repo()
    if not repo: return
    if 'origin' in repo.remotes:
        try:
            repo.remotes.origin.push()
        except git.GitCommandError as e:
            ui.echo_error(f"Failed to push to remote 'origin': {e.stderr}")
    else:
        ui.echo_warning("Remote 'origin' not configured. Skipping push.")