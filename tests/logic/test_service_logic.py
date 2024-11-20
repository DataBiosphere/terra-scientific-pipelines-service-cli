# tests/logic/test_service_logic.py

import pytest
from mockito import when, mock, verify

from teaspoons_client import ApiException

from terralab.logic import service_logic

from tests.utils_for_tests import capture_logs


@pytest.fixture
def mock_cli_config(unstub):
    config = mock({"token_file": "mock_token_file"})
    when(service_logic).CliConfig(...).thenReturn(config)
    yield config
    unstub()
