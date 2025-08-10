from src import initializer, vcs

def test_run_initialization_success_no_gpg(mocker, setup_fs):
    mock_run_command = mocker.patch('src.system.run_command')
    mocker.patch('src.system.check_dependencies', return_value=True)
    mocker.patch('src.ui.prompt_yes_no', return_value=False)
    mocker.patch('src.vcs.add_files')
    mocker.patch('src.vcs.commit')

    def run_command_side_effect(*args, **kwargs):
        command = args[0]
        if command[0] == "age-keygen" and "-y" in command:
            return mocker.Mock(stdout="age1testpublickey")
        return mocker.Mock(stdout="", stderr="")
        
    mock_run_command.side_effect = run_command_side_effect
    
    result = initializer.run_initialization()
    
    assert result is True
    
    with open("/config/.env", "r") as f:
        content = f.read()
        assert 'MASTER_AGE_KEY_STORAGE_PATH="config/keys/age-key.txt"' in content
        assert 'AGE_RECIPIENT="age1testpublickey"' in content