# tests/commands/test_account_commands.py

import pytest
from click.testing import CliRunner
from mockito import when, verify
from urllib.error import URLError

from terralab.commands import account_commands
from terralab.config import CliConfig
from tests.conftest import capture_logs

pytestmark = pytest.mark.usefixtures("unstub_fixture")

TEST_ACCESS_TOKEN = "test_access_token"
TEST_SHARE_GROUP = "broad-scientific-services@example.com"
TEST_PROXY_GROUP = "PROXY_1234567890@example.com"


@pytest.fixture
def mock_cli_config(unstub_fixture):
    config = CliConfig(
        client_info=None,
        teaspoons_api_url="https://not-real",
        sam_api_url="https://not-real-sam",
        server_port=12345,
        version_info_file="version_info.json",
        access_token_file="access_token",
        refresh_token_file="refresh_token",
        oauth_access_token_file="oauth_access_token",
        remote_oauth_redirect_uri="https://redirect",
        teaspoons_share_group=TEST_SHARE_GROUP,
    )
    when(account_commands).load_config().thenReturn(config)
    return config


def test_cloud_info_success(mock_cli_config, capture_logs):
    when(account_commands).get_or_refresh_access_token(mock_cli_config).thenReturn(
        TEST_ACCESS_TOKEN
    )
    when(account_commands).get_user_proxy_group(
        mock_cli_config, TEST_ACCESS_TOKEN
    ).thenReturn(TEST_PROXY_GROUP)

    runner = CliRunner()
    result = runner.invoke(account_commands.cloud_info)

    assert result.exit_code == 0
    verify(account_commands).get_or_refresh_access_token(mock_cli_config)
    verify(account_commands).get_user_proxy_group(mock_cli_config, TEST_ACCESS_TOKEN)
    assert (
        "To ensure that your cloud resources can be properly accessed by Broad Scientific Services"
        in capture_logs.text
    )
    assert TEST_SHARE_GROUP in capture_logs.text
    assert TEST_PROXY_GROUP in capture_logs.text


def test_cloud_info_sam_error(mock_cli_config, capture_logs):
    when(account_commands).get_or_refresh_access_token(mock_cli_config).thenReturn(
        TEST_ACCESS_TOKEN
    )
    when(account_commands).get_user_proxy_group(
        mock_cli_config, TEST_ACCESS_TOKEN
    ).thenRaise(URLError("connection refused"))

    runner = CliRunner()
    result = runner.invoke(account_commands.cloud_info)

    assert result.exit_code != 0
