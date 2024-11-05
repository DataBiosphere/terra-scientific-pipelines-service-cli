# tests/logic/test_submit_logic.py

import pytest
from mockito import when, mock, verify

from terralab.logic import submit_logic
from teaspoons_client.exceptions import ApiException


@pytest.fixture
def mock_cli_config(unstub):
    config = mock({"token_file": "mock_token_file"})
    when(submit_logic).CliConfig(...).thenReturn(config)
    yield config
    unstub()

