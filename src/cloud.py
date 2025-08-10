from . import ui, system, config
import datetime
import os
import tarfile

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
    
    # ОНОВЛЕНО: Створюємо архів програмно для кращого контролю над шляхами
    try:
        with tarfile.open(tar_path, "w:gz") as tar:
            # Додаємо важливі файли та папки з кореня проєкту
            # arcname='' гарантує, що вміст буде в корені архіву
            tar.add(os.path.join(config.ROOT_DIR, 'src'), arcname='src')
            tar.add(os.path.join(config.ROOT_DIR, 'config'), arcname='config')
            tar.add(os.path.join(config.ROOT_DIR, 'vault'), arcname='vault')
            tar.add(os.path.join(config.ROOT_DIR, '.gitignore'), arcname='.gitignore')
            tar.add(os.path.join(config.ROOT_DIR, 'manager.py'), arcname='manager.py')
            # Додаємо історію Git
            if os.path.isdir('.git'):
                tar.add(os.path.join(config.ROOT_DIR, '.git'), arcname='.git')

    except Exception as e:
        ui.echo_error(f"Failed to create tar archive: {e}")
        return

    ui.echo_info("Encrypting archive...")
    age_cmd = ["age", "-r", config.AGE_RECIPIENT, "-o", age_path, tar_path]
    if not system.run_command(age_cmd):
        os.remove(tar_path)
        return

    system.run_command(["shred", "-u", tar_path])

    ui.echo_info("Uploading to cloud remotes...")
    for remote in config.CLOUD_REMOTES:
        ui.echo_info(f"--> Uploading to {remote}")
        rclone_cmd = ["rclone", "copy", age_path, remote, "--progress"]
        system.run_command(rclone_cmd)