# tests/commands/test_account_commands.py

import pytest
from click.testing import CliRunner
from mockito import when, verify
from urllib.error import URLError

from terralab.commands import account_commands
from terralab.logic import account_logic
from tests.conftest import capture_logs

pytestmark = pytest.mark.usefixtures("unstub_fixture")

TEST_SHARE_GROUP = "broad-scientific-services@example.com"
TEST_PROXY_GROUP = "PROXY_1234567890@example.com"
TEST_ROWS = [
    ["Service Account", TEST_SHARE_GROUP],
    ["Your Proxy Group", TEST_PROXY_GROUP],
]


def test_cloud_info_success(capture_logs):
    when(account_logic).get_cloud_info().thenReturn(TEST_ROWS)

    runner = CliRunner()
    result = runner.invoke(account_commands.cloud_info)

    assert result.exit_code == 0
    verify(account_logic).get_cloud_info()
    assert (
        "To ensure that your cloud resources can be properly accessed by Broad Scientific Services"
        in capture_logs.text
    )
    assert TEST_SHARE_GROUP in capture_logs.text
    assert TEST_PROXY_GROUP in capture_logs.text


def test_cloud_info_sam_error():
    when(account_logic).get_cloud_info().thenRaise(URLError("connection refused"))

    runner = CliRunner()
    result = runner.invoke(account_commands.cloud_info)

    assert result.exit_code != 0
