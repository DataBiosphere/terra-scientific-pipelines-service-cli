# tests/test_config

import pytest
from mockito import mock, when
from pathlib import Path

from terralab import config


def test_config():
    mock_client_info = mock()
    when(config.OAuth2ClientInfo).from_oidc_endpoint(
        "https://dontcare",
        client_id="whatever",
        scopes=["offline_access+email+profile+whatever"],
    ).thenReturn(mock_client_info)

    test_config = config.load_config(config_file=".test.config", package="tests")

    assert test_config.teaspoons_api_url == "not-real"
    assert test_config.access_token_file == f"{Path.home()}/.cool/access_token"
    assert test_config.refresh_token_file == f"{Path.home()}/.cool/refresh_token"
    assert test_config.oauth_token_file == f"{Path.home()}/.cool/oauth_token"

    assert test_config.server_port == 12345
    assert test_config.client_info == mock_client_info


def test_config_missing_api_url():
    mock_client_info = mock()
    when(config.OAuth2ClientInfo).from_oidc_endpoint(
        "https://dontcare",
        client_id="whatever",
        scopes=["offline_access+email+profile+whatever"],
    ).thenReturn(mock_client_info)

    with pytest.raises(RuntimeError):
        config.load_config(config_file=".test.missing_api_url.config", package="tests")


def test_config_missing_server_port():
    mock_client_info = mock()
    when(config.OAuth2ClientInfo).from_oidc_endpoint(
        "https://dontcare",
        client_id="whatever",
        scopes=["offline_access+email+profile+whatever"],
    ).thenReturn(mock_client_info)

    with pytest.raises(RuntimeError):
        config.load_config(
            config_file=".test.missing_server_port.config", package="tests"
        )
