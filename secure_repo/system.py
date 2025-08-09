import subprocess
import shutil
import platform
import os
import tarfile
import tempfile
import urllib.request
from . import ui
import click

# run_command та _install_rclone залишаються без змін
def run_command(command, capture=False, shell=False):
    # ... (код без змін)
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=capture,
            text=True,
            encoding='utf-8',
            shell=shell
        )
        return result
    except FileNotFoundError:
        ui.echo_error(f"Command not found: {command[0]}")
        return None
    except subprocess.CalledProcessError as e:
        ui.echo_error(f"Error executing command: {' '.join(command)}")
        ui.echo_error(e.stderr or e.stdout)
        return None

def _install_rclone():
    # ... (код без змін)
    ui.echo_info("To install rclone, please run the following command in your terminal:")
    ui.echo_warning("  curl https://rclone.org/install.sh | sudo bash")
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
    
    # --- ВИПРАВЛЕННЯ ---
    # Створюємо тимчасову директорію, яка НЕ буде видалена автоматично
    # tempfile.mkdtemp() просто створює директорію і повертає шлях до неї
    tmpdir = tempfile.mkdtemp()
    
    tar_path = os.path.join(tmpdir, "age.tar.gz")
    ui.echo_info(f"Downloading: {url}")
    try:
        urllib.request.urlretrieve(url, tar_path)
        ui.echo_success(f"Successfully downloaded to {tar_path}")
    except Exception as e:
        ui.echo_error(f"Failed to download age: {e}")
        # Прибираємо за собою у випадку помилки
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
    
    # Попереджаємо користувача, що потрібно прибрати за собою
    ui.echo_warning(f"After installation, you can manually delete the temporary directory:")
    ui.echo_warning(f"  rm -rf {tmpdir}")
    ui.echo_info("Now, please start this script again.")

    return False

# функція check_dependencies залишається без змін
def check_dependencies():
    # ... (код без змін)
    deps = {
        "git": None,
        "age": _install_age,
        "gpg": None,
        "rclone": _install_rclone,
        "shred": None,
    }
    
    final_ok = True
    for dep, install_func in deps.items():
        if shutil.which(dep):
            ui.echo_success(f"{dep} found.")
        else:
            ui.echo_error(f"{dep} NOT found.")
            final_ok = False
            if install_func:
                if ui.prompt_yes_no(f"Do you want to see instructions to install '{dep}'?"):
                    install_func()
            else:
                ui.echo_warning(f"Please install '{dep}' manually using your system's package manager (e.g., 'sudo dnf install {dep}' or 'sudo apt-get install {dep}').")
    
    if final_ok:
        ui.echo_success("All dependencies are met.")
    else:
        click.echo("")
        ui.echo_error("Some dependencies are missing. Please install them and run the script again.")

    return final_ok