# tests/logic/test_auth_logic.py

import pytest
from mockito import when, mock, verify

from terralab.logic import auth_logic
from tests.conftest import capture_logs

pytestmark = pytest.mark.usefixtures("unstub_fixture")


@pytest.fixture
def mock_cli_config(unstub):
    config = mock(
        {
            "access_token_file": "mock_access_token_file",
            "refresh_token_file": "mock_refresh_token_file",
            "oauth_access_token_file": "mock_oauth_access_token_file",
            "client_info": "mock_client_info",
        }
    )
    when(auth_logic).load_config(...).thenReturn(config)
    yield config
    unstub()


def test_clear_local_tokens(mock_cli_config, capture_logs):
    when(auth_logic)._clear_local_token(...).thenReturn(None)

    auth_logic.clear_local_tokens()  # default is verbose = True

    verify(auth_logic)._clear_local_token("mock_access_token_file")
    verify(auth_logic)._clear_local_token("mock_refresh_token_file")
    verify(auth_logic)._clear_local_token("mock_oauth_access_token_file")

    assert "Logged out" in capture_logs.text


def test_clear_local_tokens_no_print(mock_cli_config, capture_logs):
    when(auth_logic)._clear_local_token(...).thenReturn(None)

    auth_logic.clear_local_tokens(verbose=False)

    verify(auth_logic)._clear_local_token("mock_access_token_file")
    verify(auth_logic)._clear_local_token("mock_refresh_token_file")
    verify(auth_logic)._clear_local_token("mock_oauth_access_token_file")

    assert "Logged out" not in capture_logs.text


def test_login_with_oauth(mock_cli_config):
    test_token = "fake token"
    when(auth_logic)._save_local_token(...)

    auth_logic.login_with_oauth(test_token)

    verify(auth_logic)._save_local_token("mock_oauth_access_token_file", test_token)


def test_login_with_custom_redirect(mock_cli_config):
    test_access_token = "fake access token"
    test_refresh_token = "fake refresh token"

    when(auth_logic).get_tokens_with_custom_redirect(mock_cli_config).thenReturn(
        (test_access_token, test_refresh_token)
    )
    when(auth_logic)._save_local_token(...)

    auth_logic.login_with_custom_redirect()

    verify(auth_logic)._save_local_token("mock_access_token_file", "fake access token")
    verify(auth_logic)._save_local_token(
        "mock_refresh_token_file", "fake refresh token"
    )
