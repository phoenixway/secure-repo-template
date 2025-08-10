from . import ui, system, config
import datetime
import os
import tarfile

def create_and_upload_backup():
    """Creates an encrypted archive and uploads it to all configured rclone remotes."""
    # ОНОВЛЕНО: Використовуємо функції для отримання конфігурації
    cloud_remotes = config.get_config("CLOUD_REMOTES")
    age_recipient = config.get_config("AGE_RECIPIENT")

    if not cloud_remotes:
        ui.echo_info("CLOUD_REMOTES not configured in .env. Skipping cloud backup.")
        return
    
    if not age_recipient:
        ui.echo_error("AGE_RECIPIENT not set. Cannot create backup.")
        return

    backup_dir = "backup"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    archive_basename = f"secure-repo-backup-{timestamp}"
    tar_path = os.path.join(backup_dir, f"{archive_basename}.tar.gz")
    age_path = f"{tar_path}.age"
    
    ui.echo_info("Creating local archive...")
    
    root_dir = config.get_root_dir()
    try:
        with tarfile.open(tar_path, "w:gz") as tar:
            # Функції для отримання шляхів використовуються неявно через config
            tar.add(os.path.join(root_dir, 'src'), arcname='src')
            tar.add(os.path.join(root_dir, 'config'), arcname='config')
            tar.add(os.path.join(root_dir, 'vault'), arcname='vault')
            tar.add(os.path.join(root_dir, '.gitignore'), arcname='.gitignore')
            tar.add(os.path.join(root_dir, 'manager.py'), arcname='manager.py')
            if os.path.isdir('.git'):
                tar.add(os.path.join(root_dir, '.git'), arcname='.git')
    except Exception as e:
        ui.echo_error(f"Failed to create tar archive: {e}")
        return

    ui.echo_info("Encrypting archive...")
    age_cmd = ["age", "-r", age_recipient, "-o", age_path, tar_path]
    if not system.run_command(age_cmd):
        os.remove(tar_path)
        return

    # Замінюємо shred на os.remove для більшої портативності
    os.remove(tar_path)

    ui.echo_info("Uploading to cloud remotes...")
    for remote in cloud_remotes:
        ui.echo_info(f"--> Uploading to {remote}")
        rclone_cmd = ["rclone", "copy", age_path, remote, "--progress"]
        system.run_command(rclone_cmd)