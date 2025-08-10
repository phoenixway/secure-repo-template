from src import github

def test_full_setup_flow_orchestration(mocker):
    """
    Тестує, що `full_setup_flow` викликає всі необхідні кроки по черзі.
    """
    # 1. Імітуємо всі внутрішні функції, які викликає `full_setup_flow`
    mock_check_auth = mocker.patch('src.github.check_gh_auth', return_value=True)
    mock_prompt = mocker.patch('click.prompt', return_value="my-test-repo")
    mock_create_key = mocker.patch('src.github.create_ssh_key', return_value=True)
    mock_create_repo = mocker.patch('src.github.create_repo', return_value="user/my-test-repo")
    mock_add_key = mocker.patch('src.github.add_deploy_key', return_value=True)
    mock_set_remote = mocker.patch('src.github.set_remote_url', return_value=True)

    # 2. Викликаємо головну функцію
    github.full_setup_flow()

    # 3. Перевіряємо, що всі кроки були викликані
    mock_check_auth.assert_called_once()
    mock_prompt.assert_called_once()
    mock_create_key.assert_called_once()
    mock_create_repo.assert_called_once_with("my-test-repo")
    mock_add_key.assert_called_once_with("user/my-test-repo")
    mock_set_remote.assert_called_once_with("user/my-test-repo")