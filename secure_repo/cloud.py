from . import ui, system, config
import datetime
import os

def create_and_upload_backup():
    """Creates an encrypted archive and uploads it to all configured rclone remotes."""
    if not config.CLOUD_REMOTES:
        ui.echo_info("CLOUD_REMOTES not configured in .env. Skipping cloud backup.")
        return
    
    if not config.AGE_RECIPIENT:
        ui.echo_error("AGE_RECIPIENT not set. Cannot create backup.")
        return

    backup_dir = "backup"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    archive_basename = f"secure-repo-backup-{timestamp}"
    tar_path = os.path.join(backup_dir, f"{archive_basename}.tar.gz")
    age_path = f"{tar_path}.age"
    
    ui.echo_info("Creating local archive...")
    # Архівуємо .git, README.md та всі *.md.age файли
    tar_cmd = ["tar", "czf", tar_path, "--exclude=.git/hooks", ".git", "README.md"]
    # Додаємо файли .md.age
    age_files = [f for f in os.listdir('.') if f.endswith('.md.age')]
    if age_files:
        tar_cmd.extend(age_files)
    
    if not system.run_command(tar_cmd):
        return # Помилка при створенні архіву

    ui.echo_info("Encrypting archive...")
    age_cmd = ["age", "-r", config.AGE_RECIPIENT, "-o", age_path, tar_path]
    if not system.run_command(age_cmd):
        os.remove(tar_path) # Прибираємо за собою
        return

    # Безпечно видаляємо незашифрований архів
    system.run_command(["shred", "-u", tar_path])

    ui.echo_info("Uploading to cloud remotes...")
    for remote in config.CLOUD_REMOTES:
        ui.echo_info(f"--> Uploading to {remote}")
        rclone_cmd = ["rclone", "copy", age_path, remote, "--progress"]
        system.run_command(rclone_cmd)