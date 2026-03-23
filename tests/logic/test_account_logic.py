# tests/logic/test_account_logic.py

import pytest
from mockito import mock, when
from urllib.error import URLError

from terralab.logic import account_logic

pytestmark = pytest.mark.usefixtures("unstub_fixture")

TEST_ACCESS_TOKEN = "test_access_token"
TEST_SHARE_GROUP = "broad-scientific-services@example.com"
TEST_PROXY_GROUP = "PROXY_1234567890@example.com"


@pytest.fixture
def mock_cli_config():
    config = mock({"teaspoons_share_group": TEST_SHARE_GROUP})
    return config


def test_get_cloud_info_success(mock_cli_config):
    when(account_logic).get_user_proxy_group(
        mock_cli_config, TEST_ACCESS_TOKEN
    ).thenReturn(TEST_PROXY_GROUP)

    result = account_logic.get_cloud_info(mock_cli_config, TEST_ACCESS_TOKEN)

    assert result == [
        ["Service Account", TEST_SHARE_GROUP],
        ["Your Proxy Group", TEST_PROXY_GROUP],
    ]


def test_get_cloud_info_sam_error(mock_cli_config):
    when(account_logic).get_user_proxy_group(
        mock_cli_config, TEST_ACCESS_TOKEN
    ).thenRaise(URLError("connection refused"))

    with pytest.raises(URLError):
        account_logic.get_cloud_info(mock_cli_config, TEST_ACCESS_TOKEN)
