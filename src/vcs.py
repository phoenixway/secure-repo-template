from . import ui, config
import git
import os
from datetime import datetime

def _get_repo():
    """Initializes and returns a repo object using the dynamic root path."""
    try:
        return git.Repo(config.get_root_dir(), search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        return None

def has_changes():
    """Checks if there are any changes."""
    repo = _get_repo()
    if not repo: return False
    return repo.is_dirty(untracked_files=True)

def add():
    """Adds all relevant files from vault/ to the Git index."""
    repo = _get_repo()
    if not repo: return
    
    # ОНОВЛЕНО: Використовуємо функції для отримання шляхів
    vault_dir = config.get_vault_dir()
    root_dir = config.get_root_dir()
    
    files_to_add = []
    if os.path.isdir(vault_dir):
        files_to_add = [os.path.join(vault_dir, f) for f in os.listdir(vault_dir) if f.endswith('.md.age')]

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
    """Adds a specific list of files and directories to the Git index."""
    repo = _get_repo()
    if not repo: return
    try:
        # ОНОВЛЕНО: Використовуємо функцію для отримання шляху
        relative_paths = [os.path.relpath(p, config.get_root_dir()) for p in files_to_add]
        repo.index.add(relative_paths)
        ui.echo_info(f"Added {len(relative_paths)} item(s) to index.")
    except git.GitCommandError as e:
        ui.echo_error(f"Failed to add files to Git: {e}")

def commit(message):
    """Commits staged changes with a timestamp."""
    repo = _get_repo()
    if not repo: return
    full_message = f"{message} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    repo.index.commit(full_message)

def push():
    """Pushes changes to the remote 'origin'."""
    repo = _get_repo()
    if not repo: return
    if 'origin' in repo.remotes:
        try:
            repo.remotes.origin.push()
        except git.GitCommandError as e:
            ui.echo_error(f"Failed to push to remote 'origin': {e.stderr}")
    else:
        ui.echo_warning("Remote 'origin' not configured. Skipping push.")