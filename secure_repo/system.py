import subprocess
import shutil
from . import ui

def run_command(command, capture=False):
    """A helper to run external commands."""
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=capture,
            text=True,
            encoding='utf-8'
        )
        return result
    except FileNotFoundError:
        ui.echo_error(f"Command not found: {command[0]}")
        return None
    except subprocess.CalledProcessError as e:
        ui.echo_error(f"Error executing command: {' '.join(command)}")
        ui.echo_error(e.stderr or e.stdout)
        return None

def check_dependencies():
    """Checks for required system dependencies."""
    deps = ["git", "age", "gpg", "rclone", "shred"]
    all_found = True
    for dep in deps:
        if shutil.which(dep):
            ui.echo_success(f"{dep} found.")
        else:
            ui.echo_error(f"{dep} NOT found. Please install it.")
            all_found = False
    return all_found