from src import decryptor, config
import os

def test_run_decryption_success(mocker, setup_fs):
    fs = setup_fs
    fs.create_file("/vault/note1.md.age")
    fs.create_file("/config/keys/key.txt")
    
    def config_side_effect(key):
        if key == "MASTER_KEY_PATH":
            return "/config/keys/key.txt"
        return None
    mocker.patch('src.config.get_config', side_effect=config_side_effect)
    
    mocker.patch('shutil.which', return_value=True)
    mock_run_command = mocker.patch('src.system.run_command')
    mock_fzf_result = mocker.Mock(stdout="note1.md.age\n")
    
    def run_command_side_effect(*args, **kwargs):
        command = args[0]
        if command[0] == 'fzf': return mock_fzf_result
        if command[0] == 'age':
            fs.create_file("/vault/note1.md", contents="decrypted data")
            return mocker.Mock(stdout="", stderr="")
        return mocker.Mock(stdout="", stderr="")

    mock_run_command.side_effect = run_command_side_effect
    
    decryptor.run_decryption()
    
    assert os.path.exists("/vault/note1.md")

def test_decryption_aborts_if_no_files_selected(mocker, setup_fs):
    fs = setup_fs
    fs.create_file("/vault/note1.md.age")
    fs.create_file("/config/keys/key.txt")
    mocker.patch('src.config.get_config', return_value="/config/keys/key.txt")
    mocker.patch('shutil.which', return_value=True)

    mock_fzf_result = mocker.Mock(stdout="")
    mock_run_command = mocker.patch('src.system.run_command', return_value=mock_fzf_result)
    
    decryptor.run_decryption()
    
    mock_run_command.assert_called_once()