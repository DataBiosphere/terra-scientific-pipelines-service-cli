# tests/logic/test_auth_logic.py

import pytest
from mockito import when, mock, verify

from terralab.logic import auth_logic


@pytest.fixture
def mock_cli_config(unstub):
    config = mock(
        {
            "access_token_file": "mock_access_token_file",
            "refresh_token_file": "mock_refresh_token_file",
            "oauth_token_file": "mock_oauth_token_file",
            "client_info": "mock_client_info",
        }
    )
    when(auth_logic).load_config(...).thenReturn(config)
    yield config
    unstub()


def test_clear_local_token(mock_cli_config, unstub):
    when(auth_logic)._clear_local_token(...).thenReturn(None)

    auth_logic.clear_local_token()

    verify(auth_logic)._clear_local_token("mock_access_token_file")
    verify(auth_logic)._clear_local_token("mock_refresh_token_file")
    verify(auth_logic)._clear_local_token("mock_oauth_token_file")


def test_login_with_oauth(mock_cli_config, unstub):
    test_token = "fake token"
    when(auth_logic)._save_local_token(...)

    auth_logic.login_with_oauth(test_token)

    verify(auth_logic)._save_local_token("mock_oauth_token_file", test_token)
