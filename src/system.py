import subprocess
import shutil
import platform
import os
import tarfile
import tempfile
import urllib.request
from . import ui
import click

# --- ВИПРАВЛЕННЯ ТУТ ---
# Повертаємо параметр stdin_input, який потрібен для fzf
def run_command(command, capture=False, shell=False, stdin_input=None):
    """A helper to run external commands, with optional stdin."""
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=capture,
            text=True,
            encoding='utf-8',
            shell=shell,
            input=stdin_input # Використовуємо цей параметр
        )
        return result
    except FileNotFoundError:
        ui.echo_error(f"Command not found: {command[0]}")
        return None
    except subprocess.CalledProcessError as e:
        ui.echo_error(f"Error executing command: {' '.join(command)}")
        # Показуємо stderr якщо він є, інакше stdout
        output = e.stderr or e.stdout
        if output:
            ui.echo_error(output)
        return None

# Решта файлу залишається без змін
def _install_rclone():
    """Provides instructions for installing rclone."""
    ui.echo_info("To install rclone, please run the following command in your terminal:")
    ui.echo_warning("  curl https://rclone.org/install.sh | sudo bash")
    return False 

def _install_gh():
    """Provides instructions to install the GitHub CLI."""
    ui.echo_info("To automate GitHub operations, the official GitHub CLI ('gh') is required.")
    ui.echo_info("Please install it by following the instructions for your OS:")
    ui.echo_warning("  https://github.com/cli/cli#installation")
    return False



def _install_age():
    """Downloads age and provides the user with commands to install it."""
    ui.echo_info("Attempting to download 'age' from GitHub releases...")
    
    os_type = platform.system().lower()
    arch = platform.machine()
    version = "v1.2.0"

    if arch == "x86_64":
        arch = "amd64"
    elif arch == "aarch64":
        arch = "arm64"
    else:
        ui.echo_error(f"Unsupported architecture: {arch}")
        return False

    url = f"https://github.com/FiloSottile/age/releases/download/{version}/age-{version}-{os_type}-{arch}.tar.gz"
    
    tmpdir = tempfile.mkdtemp()
    
    tar_path = os.path.join(tmpdir, "age.tar.gz")
    ui.echo_info(f"Downloading: {url}")
    try:
        urllib.request.urlretrieve(url, tar_path)
        ui.echo_success(f"Successfully downloaded to {tar_path}")
    except Exception as e:
        ui.echo_error(f"Failed to download age: {e}")
        shutil.rmtree(tmpdir)
        return False

    ui.echo_info("Extracting archive...")
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=tmpdir)
    except tar.TarError as e:
        ui.echo_error(f"Failed to extract archive: {e}")
        shutil.rmtree(tmpdir)
        return False

    age_dir = os.path.join(tmpdir, "age")
    
    ui.echo_step("To complete the installation, please copy and run these commands:")
    
    install_instructions = f"""
# --- Start of commands ---
sudo mv "{age_dir}/age" /usr/local/bin/
sudo mv "{age_dir}/age-keygen" /usr/local/bin/
# --- End of commands ---
"""
    click.echo(click.style(install_instructions, fg="yellow"))
    
    ui.echo_warning(f"After installation, you can manually delete the temporary directory:")
    ui.echo_warning(f"  rm -rf {tmpdir}")
    ui.echo_info("Now, please start this script again.")

    return False

def _install_fzf():
    """
    Installs fzf by cloning the official repository and running the install script.
    """
    if not shutil.which("git"):
        ui.echo_error("Git is not installed, which is required to auto-install fzf.")
        ui.echo_warning("Please install 'git' first, then try again.")
        return False

    ui.echo_info("fzf can be installed from its official git repository.")
    if ui.prompt_yes_no("Do you want to proceed with fzf installation?"):
        fzf_dir = os.path.expanduser("~/.fzf")
        
        if os.path.exists(fzf_dir):
            ui.echo_warning(f"Directory {fzf_dir} already exists. Skipping clone.")
        else:
            clone_cmd = ["git", "clone", "--depth", "1", "https://github.com/junegunn/fzf.git", fzf_dir]
            if not run_command(clone_cmd):
                ui.echo_error("Failed to clone fzf repository.")
                return False
        
        ui.echo_info("Running fzf installation script. It may ask you some questions.")
        ui.echo_warning("Answer 'y' to enable fuzzy completion and key bindings for the best experience.")
        
        install_script_path = os.path.join(fzf_dir, "install")
        if run_command([install_script_path]):
            ui.echo_success("fzf installation script finished.")
            ui.echo_warning("Please restart your terminal session for fzf to be available in PATH.")
            return True
        else:
            ui.echo_error("fzf installation script failed.")
            return False
    return False

def check_dependencies():
    """Checks for dependencies and offers to install them if missing."""
    deps = {
        "git": None,
        "age": _install_age,
        "gpg": None,
        "rclone": _install_rclone,
        "shred": None,
        "fzf": _install_fzf,
        "gh": _install_gh,
    }
    
    final_ok = True
    for dep, install_func in deps.items():
        if shutil.which(dep):
            ui.echo_success(f"{dep} found.")
        else:
            ui.echo_error(f"{dep} NOT found.")
            final_ok = False
            if install_func:
                if ui.prompt_yes_no(f"Do you want help installing '{dep}'?"):
                    install_func()
            else:
                ui.echo_warning(f"Please install '{dep}' manually using your system's package manager (e.g., 'sudo dnf install {dep}' or 'sudo apt-get install {dep}').")
    
    if final_ok:
        ui.echo_success("All dependencies are met.")
    else:
        click.echo("")
        ui.echo_error("Some dependencies are missing. Please install them and run the script again.")

    return final_ok