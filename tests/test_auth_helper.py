# tests/test_auth_helper.py

import builtins
import logging
import os

import pytest
from jwt import ExpiredSignatureError
from mockito import when, mock, verify, times
from oauth2_cli_auth._timeout import TimeoutException

from terralab import auth_helper
from tests.utils_for_tests import capture_logs

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def mock_cli_config(unstub):
    config = mock(
        {
            "access_token_file": "mock_access_token_file",
            "refresh_token_file": "mock_refresh_token_file",
            "oauth_token_file": "mock_oauth_token_file",
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


def test_get_or_refresh_access_token_valid_oauth(mock_cli_config, unstub):
    test_oauth_token = "oauth token"

    # mock an existing oauth token
    when(auth_helper)._load_local_token(
        "mock_oauth_token_file", validate=False
    ).thenReturn(test_oauth_token)

    assert auth_helper.get_or_refresh_access_token(mock_cli_config) == test_oauth_token
    unstub()


def test_get_or_refresh_access_token_valid_access(mock_cli_config, unstub):
    test_access_token = "access token"
    test_refresh_token = "refresh token"

    # mock a valid access token
    when(auth_helper)._load_local_token(
        "mock_oauth_token_file", validate=False
    ).thenReturn(None)
    when(auth_helper)._load_local_token("mock_access_token_file").thenReturn(
        test_access_token
    )
    when(auth_helper)._load_local_token(
        "mock_refresh_token_file", validate=False
    ).thenReturn(test_refresh_token)

    assert auth_helper.get_or_refresh_access_token(mock_cli_config) == test_access_token
    unstub()


def test_get_or_refresh_access_token_valid_refresh(mock_cli_config, unstub):
    test_refresh_token = "refresh token"
    test_new_access_token = "access token"
    test_new_refresh_token = "new refresh token"

    # mock no valid access token, but find a refresh token
    when(auth_helper)._load_local_token(
        "mock_oauth_token_file", validate=False
    ).thenReturn(None)
    when(auth_helper)._load_local_token("mock_access_token_file").thenReturn(None)
    when(auth_helper)._load_local_token(
        "mock_refresh_token_file", validate=False
    ).thenReturn(test_refresh_token)

    # mock a successful call to refresh_tokens
    when(auth_helper).refresh_tokens(mock_cli_config, test_refresh_token).thenReturn(
        tuple([test_new_access_token, test_new_refresh_token])
    )

    when(auth_helper)._save_local_token("mock_access_token_file", test_new_access_token)
    when(auth_helper)._save_local_token(
        "mock_refresh_token_file", test_new_refresh_token
    )

    assert (
        auth_helper.get_or_refresh_access_token(mock_cli_config)
        == test_new_access_token
    )
    unstub()


def test_get_or_refresh_access_token_failed_refresh(mock_cli_config, unstub):
    test_refresh_token = "refresh token"
    test_new_access_token = "access token"
    test_new_refresh_token = "new refresh token"

    # mock no valid access token, but find a refresh token
    when(auth_helper)._load_local_token(
        "mock_oauth_token_file", validate=False
    ).thenReturn(None)
    when(auth_helper)._load_local_token("mock_access_token_file").thenReturn(None)
    when(auth_helper)._load_local_token(
        "mock_refresh_token_file", validate=False
    ).thenReturn(test_refresh_token)

    # mock a failed call to refresh_tokens
    when(auth_helper).refresh_tokens(mock_cli_config, test_refresh_token).thenRaise(
        TimeoutException
    )

    # mock a successful call to get new tokens via browser
    when(auth_helper).get_tokens_with_browser_open(mock_cli_config).thenReturn(
        tuple([test_new_access_token, test_new_refresh_token])
    )

    when(auth_helper)._save_local_token("mock_access_token_file", test_new_access_token)
    when(auth_helper)._save_local_token(
        "mock_refresh_token_file", test_new_refresh_token
    )

    assert (
        auth_helper.get_or_refresh_access_token(mock_cli_config)
        == test_new_access_token
    )
    unstub()


def test_get_or_refresh_access_token_none_found(mock_cli_config, unstub):
    test_new_access_token = "access token"
    test_new_refresh_token = "new refresh token"

    # mock no valid access token, no refresh token
    when(auth_helper)._load_local_token(
        "mock_oauth_token_file", validate=False
    ).thenReturn(None)
    when(auth_helper)._load_local_token("mock_access_token_file").thenReturn(None)
    when(auth_helper)._load_local_token(
        "mock_refresh_token_file", validate=False
    ).thenReturn(None)

    # mock a successful call to get new tokens via browser
    when(auth_helper).get_tokens_with_browser_open(mock_cli_config).thenReturn(
        tuple([test_new_access_token, test_new_refresh_token])
    )

    when(auth_helper)._save_local_token("mock_access_token_file", test_new_access_token)
    when(auth_helper)._save_local_token(
        "mock_refresh_token_file", test_new_refresh_token
    )

    assert (
        auth_helper.get_or_refresh_access_token(mock_cli_config)
        == test_new_access_token
    )
    unstub()


def test_get_access_token_with_browser_open_valid_code(mock_cli_config, unstub):
    mock_callback_server = mock()
    mock_code = mock()
    expected_access_token = "accesstoken"
    expected_refresh_token = "refreshtoken"
    exchange_response_dict = {
        "access_token": expected_access_token,
        "refresh_token": expected_refresh_token,
    }

    when(auth_helper).CustomOAuthCallbackHttpServer(
        mock_cli_config.server_port
    ).thenReturn(mock_callback_server)
    when(auth_helper).get_auth_url(...).thenReturn(None)
    when(auth_helper)._open_browser(...).thenReturn(None)
    when(mock_callback_server).wait_for_code().thenReturn(mock_code)
    when(auth_helper)._exchange_code_for_response(...).thenReturn(
        exchange_response_dict
    )

    access_token, refresh_token = auth_helper.get_tokens_with_browser_open(
        mock_cli_config
    )

    assert access_token == expected_access_token
    assert refresh_token == expected_refresh_token

    unstub()


def test_get_access_token_with_browser_open_no_code(mock_cli_config, unstub):
    mock_callback_server = mock()

    when(auth_helper).CustomOAuthCallbackHttpServer(
        mock_cli_config.server_port
    ).thenReturn(mock_callback_server)
    when(auth_helper).get_auth_url(...).thenReturn(None)
    when(auth_helper)._open_browser(...).thenReturn(None)
    when(mock_callback_server).wait_for_code().thenReturn(None)

    with pytest.raises(ValueError):
        auth_helper.get_tokens_with_browser_open(mock_cli_config)

    unstub()


def test_open_browser(capture_logs, unstub):
    test_url = "http://test/url"

    when(auth_helper.webbrowser).open(test_url)  # do nothing

    # nothing should print
    auth_helper._open_browser(test_url, None)
    assert "" == capture_logs.text

    # when you pass a logging function, a message should be logged
    auth_helper._open_browser(test_url, LOGGER.info)
    assert test_url in capture_logs.text
    unstub()


def test_refresh_tokens(mock_cli_config, unstub):
    test_refresh_token = "refresh token"
    new_access_token = "new access token"
    new_refresh_token = "new refresh token"
    expected_response_dict = {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
    }

    mock_callback_url = mock()
    mock_callback_server = mock({"callback_url": mock_callback_url})

    when(auth_helper).CustomOAuthCallbackHttpServer(
        mock_cli_config.server_port
    ).thenReturn(mock_callback_server)
    when(auth_helper)._exchange_code_for_response(
        "mock_client_info",
        mock_callback_url,
        test_refresh_token,
        grant_type="refresh_token",
    ).thenReturn(expected_response_dict)

    assert auth_helper.refresh_tokens(mock_cli_config, test_refresh_token) == (
        new_access_token,
        new_refresh_token,
    )
    unstub()


def test_exchange_code_for_response_default_success(unstub):
    # test with default grant_type = "authorization_code"
    mock_token_url = "https://some/url"
    mock_client_id = "clientid"
    mock_client_info = mock({"token_url": mock_token_url, "client_id": mock_client_id})
    test_redirect_url = "https://redirect/url"
    test_code = "test code"

    # defaults: code key for test_code, grant_type is authorization_code
    expected_data_dict = {
        "code": test_code,
        "redirect_uri": test_redirect_url,
        "grant_type": "authorization_code",
    }
    mock_urlencode_output = mock()
    mock_encoded_data = mock()
    expected_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic Y2xpZW50aWQ6",  # base64 encoding of `clientid:`
    }

    expected_json_response = {}

    when(auth_helper.urllib.parse).urlencode(expected_data_dict).thenReturn(
        mock_urlencode_output
    )
    when(mock_urlencode_output).encode("utf-8").thenReturn(mock_encoded_data)

    mock_request_response = mock()
    when(auth_helper.urllib.request).Request(
        mock_token_url, data=mock_encoded_data, headers=expected_headers
    ).thenReturn(mock_request_response)
    when(auth_helper)._load_json(mock_request_response).thenReturn(
        expected_json_response
    )

    assert (
        auth_helper._exchange_code_for_response(
            mock_client_info, test_redirect_url, test_code
        )
        == expected_json_response
    )
    unstub()


def test_exchange_code_for_response_default_error(capture_logs, unstub):
    # test with default grant_type = "authorization_code"
    mock_token_url = "https://some/url"
    mock_client_id = "clientid"
    mock_client_info = mock({"token_url": mock_token_url, "client_id": mock_client_id})
    test_redirect_url = "https://redirect/url"
    test_code = "test code"

    # defaults: code key for test_code, grant_type is authorization_code
    expected_data_dict = {
        "code": test_code,
        "redirect_uri": test_redirect_url,
        "grant_type": "authorization_code",
    }
    mock_urlencode_output = mock()
    mock_encoded_data = mock()
    expected_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic Y2xpZW50aWQ6",  # base64 encoding of `clientid:`
    }

    # define an error response
    expected_json_response = {
        "error": "some error",
        "error_description": "more about the error",
    }

    when(auth_helper.urllib.parse).urlencode(expected_data_dict).thenReturn(
        mock_urlencode_output
    )
    when(mock_urlencode_output).encode("utf-8").thenReturn(mock_encoded_data)

    mock_request_response = mock()
    when(auth_helper.urllib.request).Request(
        mock_token_url, data=mock_encoded_data, headers=expected_headers
    ).thenReturn(mock_request_response)
    when(auth_helper)._load_json(mock_request_response).thenReturn(
        expected_json_response
    )

    assert (
        auth_helper._exchange_code_for_response(
            mock_client_info, test_redirect_url, test_code
        )
        == expected_json_response
    )
    assert (
        "Error in authentication flow exchanging code for response: some error; error description: more about the error"
        in capture_logs.text
    )
    unstub()


def test_exchange_code_for_response_refresh(capture_logs, unstub):
    # test with specified grant_type = "refresh_token"
    mock_token_url = "https://some/url"
    mock_client_id = "clientid"
    mock_client_info = mock({"token_url": mock_token_url, "client_id": mock_client_id})
    test_redirect_url = "https://redirect/url"
    test_code = "test code"

    # refresh_token instead of code key for test_code, grant type is refresh_token
    expected_data_dict = {
        "refresh_token": test_code,
        "redirect_uri": test_redirect_url,
        "grant_type": "refresh_token",
    }
    mock_urlencode_output = mock()
    mock_encoded_data = mock()
    expected_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic Y2xpZW50aWQ6",  # base64 encoding of `clientid:`
    }

    expected_json_response = {}

    when(auth_helper.urllib.parse).urlencode(expected_data_dict).thenReturn(
        mock_urlencode_output
    )
    when(mock_urlencode_output).encode("utf-8").thenReturn(mock_encoded_data)

    mock_request_response = mock()
    when(auth_helper.urllib.request).Request(
        mock_token_url, data=mock_encoded_data, headers=expected_headers
    ).thenReturn(mock_request_response)
    when(auth_helper)._load_json(mock_request_response).thenReturn(
        expected_json_response
    )

    assert (
        auth_helper._exchange_code_for_response(
            mock_client_info, test_redirect_url, test_code, "refresh_token"
        )
        == expected_json_response
    )
    assert "Token refresh successful" in capture_logs.text
    unstub()


def test_exchange_code_for_response_bad_grant_type(capture_logs, unstub):
    unexpected_grant_type = "what is this"
    with pytest.raises(SystemExit):
        auth_helper._exchange_code_for_response(
            mock(), mock(), mock(), unexpected_grant_type
        )

    assert (
        f"Authentication error: Unexpected grant_type {unexpected_grant_type}"
        in capture_logs.text
    )
    unstub()


def test_validate_token_valid(unstub):
    access_token = "accesstoken"

    when(auth_helper.jwt).decode(access_token, ...).thenReturn(None)

    # should return True
    assert auth_helper._validate_token(access_token)
    unstub()


def test_validate_token_expired(capture_logs, unstub):
    access_token = "accesstoken"

    when(auth_helper.jwt).decode(access_token, ...).thenRaise(ExpiredSignatureError())

    # should return False
    assert not auth_helper._validate_token(access_token)
    assert "expired" in capture_logs.text
    unstub()


def test_validate_token_other_error(capture_logs, unstub):
    access_token = "accesstoken"

    when(auth_helper.jwt).decode(access_token, ...).thenRaise(ValueError())

    # should return False
    assert not auth_helper._validate_token(access_token)
    assert "Error validating token" in capture_logs.text
    unstub()


def test_clear_local_token_success(unstub):
    mock_access_token_file = mock()

    when(auth_helper.os).remove(mock_access_token_file).thenReturn(None)

    auth_helper._clear_local_token(mock_access_token_file)

    verify(auth_helper.os).remove(mock_access_token_file)
    unstub()


def test_clear_local_token_not_found(capture_logs, unstub):
    mock_access_token_file = mock()

    when(auth_helper.os).remove(mock_access_token_file).thenRaise(FileNotFoundError())

    auth_helper._clear_local_token(mock_access_token_file)

    assert "No local token found to clean up" in capture_logs.text
    unstub()


def test_load_local_token_success(mock_builtin_open, unstub):
    mock_access_token_file = mock()
    expected_access_token = "accesstoken"

    when(mock_builtin_open).read().thenReturn(expected_access_token)
    when(auth_helper)._validate_token(expected_access_token).thenReturn(True)

    assert (
        auth_helper._load_local_token(mock_access_token_file) == expected_access_token
    )
    unstub()


def test_load_local_token_invalid(mock_builtin_open, unstub):
    mock_access_token_file = mock()
    expected_access_token = "accesstoken"

    when(mock_builtin_open).read().thenReturn(expected_access_token)
    when(auth_helper)._validate_token(expected_access_token).thenReturn(False)

    assert auth_helper._load_local_token(mock_access_token_file) is None
    unstub()


def test_load_local_token_do_not_validate(mock_builtin_open, unstub):
    mock_access_token_file = mock()

    expected_access_token = "accesstoken"

    when(mock_builtin_open).read().thenReturn(expected_access_token)
    when(auth_helper)._validate_token(...)

    assert (
        auth_helper._load_local_token(mock_access_token_file, validate=False)
        == expected_access_token
    )

    # validate function should not have been called
    verify(auth_helper, times(0))._validate_token()
    unstub()


def test_load_local_token_file_not_found(mock_builtin_open, unstub):
    mock_access_token_file = mock()

    when(mock_builtin_open).read().thenRaise(FileNotFoundError())
    when(auth_helper)._clear_local_token(mock_access_token_file).thenReturn(None)

    assert auth_helper._load_local_token(mock_access_token_file) is None
    unstub()


def test_save_local_token(mock_builtin_open, unstub):
    mock_access_token_file = mock()
    mock_token = mock()
    mock_dirname = mock()
    mock_descriptor = mock()

    when(auth_helper.os.path).dirname(mock_access_token_file).thenReturn(mock_dirname)
    when(auth_helper.os).makedirs(mock_dirname, exist_ok=True).thenReturn(None)
    when(auth_helper.os).open(
        mock_access_token_file, os.O_WRONLY | os.O_CREAT, 0o600
    ).thenReturn(mock_descriptor)

    mock_fdopen = mock()
    when(mock_fdopen).__enter__().thenReturn(mock_fdopen)
    when(mock_fdopen).__exit__(None, None, None).thenReturn(None)
    when(auth_helper.os).fdopen(mock_descriptor, "w").thenReturn(mock_fdopen)

    when(mock_fdopen).write().thenReturn(None)

    auth_helper._save_local_token(mock_access_token_file, mock_token)

    verify(auth_helper.os).makedirs(mock_dirname, exist_ok=True)
    unstub()
