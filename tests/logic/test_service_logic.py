# tests/logic/test_service_logic.py

import pytest
from mockito import when, mock, verify

from teaspoons_client import VersionProperties

from terralab.logic import service_logic

from tests.utils_for_tests import capture_logs


@pytest.fixture
def mock_cli_config(unstub):
    config = mock({"token_file": "mock_token_file"})
    when(service_logic).CliConfig(...).thenReturn(config)
    yield config
    unstub()


@pytest.fixture
def mock_client_wrapper(unstub):
    client = mock()
    # Make the mock support context manager protocol
    when(client).__enter__().thenReturn(client)
    when(client).__exit__(None, None, None).thenReturn(None)

    when(service_logic).ClientWrapper(...).thenReturn(client)
    yield client
    unstub()


@pytest.fixture
def mock_service_api(mock_client_wrapper, unstub):
    api = mock()
    when(service_logic).PublicApi(...).thenReturn(api)
    yield api
    unstub()


def test_get_version(mock_service_api):
    test_version = VersionProperties()
    when(mock_service_api).get_version().thenReturn(test_version)

    assert service_logic.get_version() == test_version


def test_get_status(mock_service_api):
    # 200 / running
    status_ok = mock({"status_code": 200, "data": None})
    when(mock_service_api).get_status_with_http_info().thenReturn(status_ok)

    assert service_logic.get_status() == "Running"

    # 500 / internal error
    status_500 = mock({"status_code": 500, "data": "error message"})
    when(mock_service_api).get_status_with_http_info().thenReturn(status_500)

    assert service_logic.get_status() == "error message"
