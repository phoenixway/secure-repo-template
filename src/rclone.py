# src/rclone.py
import os
import shutil
import tempfile
from . import ui, system, config, decryptor

def run_restore():
    """Handles restoring the repository from a cloud archive."""
    if not shutil.which("rclone"):
        ui.echo_error("'rclone' is not installed. Cannot restore from cloud.")
        return

    remotes = config.get_config("CLOUD_REMOTES")
    if not remotes:
        ui.echo_error("No CLOUD_REMOTES configured in .env file.")
        return

    # TODO: Add interactive selection for multiple remotes
    selected_remote = remotes[0]
    ui.echo_info(f"Searching for backups on remote: {selected_remote}")

    list_cmd = ["rclone", "lsf", f"{selected_remote}", "--files-only"]
    list_result = system.run_command(list_cmd, capture=True)
    if not list_result or not list_result.stdout:
        ui.echo_error(f"No backup files found on '{selected_remote}'.")
        return
        
    backup_files = [f for f in list_result.stdout.strip().split('\n') if f.endswith('.tar.gz.age')]
    if not backup_files:
        ui.echo_error(f"No compatible backup files (.tar.gz.age) found.")
        return

    fzf_input = "\n".join(backup_files)
    fzf_cmd = ["fzf", "--height=40%", "--prompt=Select a backup file to restore > "]
    fzf_result = system.run_command(fzf_cmd, capture=True, stdin_input=fzf_input)
    
    if not fzf_result or not fzf_result.stdout:
        ui.echo_info("No backup file selected. Aborting.")
        return
    
    selected_backup = fzf_result.stdout.strip()
    
    identity_file, temp_key_handle = decryptor._get_identity_file()
    if not identity_file:
        return
        
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            downloaded_archive_path = os.path.join(tmpdir, selected_backup)
            decrypted_tar_path = downloaded_archive_path.replace('.age', '')
            
            ui.echo_step(f"1/3: Downloading '{selected_backup}'...")
            download_cmd = ["rclone", "copy", f"{selected_remote}/{selected_backup}", tmpdir, "--progress"]
            if not system.run_command(download_cmd): return

            ui.echo_step(f"2/3: Decrypting archive...")
            decrypt_cmd = ["age", "-d", "-i", identity_file, "-o", decrypted_tar_path, downloaded_archive_path]
            if not system.run_command(decrypt_cmd): return
            
            restore_dir = f"restored_backup_{os.path.basename(decrypted_tar_path).replace('.tar.gz', '')}"
            os.makedirs(restore_dir, exist_ok=True)
            
            ui.echo_step(f"3/3: Extracting files to '{restore_dir}'...")
            extract_cmd = ["tar", "-xzf", decrypted_tar_path, "-C", restore_dir]
            if not system.run_command(extract_cmd): return

            ui.echo_success(f"\nRestore complete! Files are in: ./{restore_dir}")
    finally:
        if temp_key_handle:
            temp_key_handle.close()