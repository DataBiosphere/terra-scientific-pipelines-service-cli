# tests/test_auth_helper.py

import builtins
import logging
import pytest
from mockito import when, mock, verify
from jwt import ExpiredSignatureError

from terralab import auth_helper
from tests.utils_for_tests import capture_logs

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def mock_cli_config(unstub):
    config = mock(
        {
            "token_file": "mock_token_file",
            "client_info": "mock_client_info",
            "server_port": "0",
        }
    )
    when(auth_helper).CliConfig(...).thenReturn(config)
    yield config
    unstub()


@pytest.fixture
def mock_builtin_open(unstub):
    mock_open = mock()
    # Make the mock support context manager protocol
    when(mock_open).__enter__().thenReturn(mock_open)
    when(mock_open).__exit__(None, None, None).thenReturn(None)

    when(builtins).open(...).thenReturn(mock_open)
    yield mock_open
    unstub()


def test_get_access_token_with_browser_open_valid_code(mock_cli_config):
    mock_client_info = mock()
    mock_callback_server = mock()
    mock_code = mock()
    mock_token = mock()

    when(auth_helper).OAuthCallbackHttpServer(mock_cli_config.server_port).thenReturn(
        mock_callback_server
    )
    when(auth_helper).get_auth_url(...).thenReturn(None)
    when(auth_helper)._open_browser(...).thenReturn(None)
    when(mock_callback_server).wait_for_code().thenReturn(mock_code)
    when(auth_helper).exchange_code_for_access_token(...).thenReturn(mock_token)

    token = auth_helper.get_access_token_with_browser_open(mock_client_info)

    assert token == mock_token


def test_open_browser(capture_logs):
    test_url = "http://test/url"

    when(auth_helper.webbrowser).open(test_url)  # do nothing

    # nothing should print
    auth_helper._open_browser(test_url, None)
    assert "" == capture_logs.text

    # when you pass a logging function, a message should be logged
    auth_helper._open_browser(test_url, LOGGER.info)
    assert test_url in capture_logs.text


def test_get_access_token_with_browser_open_no_code(mock_cli_config):
    mock_client_info = mock()
    mock_callback_server = mock()

    when(auth_helper).OAuthCallbackHttpServer(mock_cli_config.server_port).thenReturn(
        mock_callback_server
    )
    when(auth_helper).get_auth_url(...).thenReturn(None)
    when(auth_helper)._open_browser(...).thenReturn(None)
    when(mock_callback_server).wait_for_code().thenReturn(None)

    with pytest.raises(ValueError):
        auth_helper.get_access_token_with_browser_open(mock_client_info)


def test_validate_token_valid():
    mock_token = mock()

    when(auth_helper.jwt).decode(mock_token, ...).thenReturn(None)

    # should return True
    assert auth_helper._validate_token(mock_token)


def test_validate_token_expired(capture_logs):
    mock_token = mock()

    when(auth_helper.jwt).decode(mock_token, ...).thenRaise(ExpiredSignatureError())

    # should return False
    assert not auth_helper._validate_token(mock_token)
    assert "Token expired" in capture_logs.text


def test_validate_token_other_error(capture_logs):
    mock_token = mock()

    when(auth_helper.jwt).decode(mock_token, ...).thenRaise(ValueError())

    # should return False
    assert not auth_helper._validate_token(mock_token)
    assert "Error validating token" in capture_logs.text


def test_clear_local_token_success():
    mock_token_file = mock()

    when(auth_helper.os).remove(mock_token_file).thenReturn(None)

    auth_helper._clear_local_token(mock_token_file)

    verify(auth_helper.os).remove(mock_token_file)


def test_clear_local_token_not_found(capture_logs):
    mock_token_file = mock()

    when(auth_helper.os).remove(mock_token_file).thenRaise(FileNotFoundError())

    auth_helper._clear_local_token(mock_token_file)

    assert "No local token found to clean up" in capture_logs.text


def test_load_local_token_success(mock_builtin_open):
    mock_token_file = mock()
    mock_token = mock()

    when(mock_builtin_open).read().thenReturn(mock_token)
    when(auth_helper)._validate_token(mock_token).thenReturn(True)

    assert auth_helper._load_local_token(mock_token_file) == mock_token


def test_load_local_token_invalid(mock_builtin_open):
    mock_token_file = mock()
    mock_token = mock()

    when(mock_builtin_open).read().thenReturn(mock_token)
    when(auth_helper)._validate_token(mock_token).thenReturn(False)

    assert auth_helper._load_local_token(mock_token_file) is None


def test_load_local_token_file_not_found(mock_builtin_open):
    mock_token_file = mock()

    when(mock_builtin_open).read().thenRaise(FileNotFoundError())
    when(auth_helper)._clear_local_token(mock_token_file).thenReturn(None)

    assert auth_helper._load_local_token(mock_token_file) is None


def test_save_local_token(mock_builtin_open):
    mock_token_file = mock()
    mock_token = mock()
    mock_dirname = mock()

    when(auth_helper.os.path).dirname(mock_token_file).thenReturn(mock_dirname)
    when(auth_helper.os).makedirs(mock_dirname, exist_ok=True).thenReturn(None)
    when(mock_builtin_open).write().thenReturn(None)

    auth_helper._save_local_token(mock_token_file, mock_token)

    verify(auth_helper.os).makedirs(mock_dirname, exist_ok=True)
