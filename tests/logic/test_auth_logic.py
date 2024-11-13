# tests/logic/test_auth_logic.py

import pytest
from mockito import when, mock, verify

from terralab.logic import auth_logic


@pytest.fixture
def mock_cli_config(unstub):
    config = mock({"token_file": "mock_token_file", "client_info": "mock_client_info"})
    when(auth_logic).CliConfig(...).thenReturn(config)
    yield config
    unstub()


def test_clear_local_token(mock_cli_config, unstub):
    when(auth_logic)._clear_local_token(...).thenReturn(None)

    auth_logic.clear_local_token()

    # Verify the token was cleared and message was printed
    verify(auth_logic)._clear_local_token("mock_token_file")
