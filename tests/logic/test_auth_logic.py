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
            "client_info": "mock_client_info",
        }
    )
    when(auth_logic).CliConfig(...).thenReturn(config)
    yield config
    unstub()


def test_clear_local_token(mock_cli_config, unstub):
    when(auth_logic)._clear_local_token(...).thenReturn(None)

    auth_logic.clear_local_token()

    verify(auth_logic)._clear_local_token("mock_access_token_file")
    verify(auth_logic)._clear_local_token("mock_refresh_token_file")
