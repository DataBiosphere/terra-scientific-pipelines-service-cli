# tests/logic/quotas_logic.py

import pytest
from mockito import mock, when
from teaspoons_client import QuotaWithDetails

from terralab.logic import quotas_logic


@pytest.fixture
def mock_cli_config(unstub):
    config = mock({"token_file": "mock_token_file"})
    when(quotas_logic).CliConfig(...).thenReturn(config)
    yield config
    unstub()


@pytest.fixture
def mock_client_wrapper(unstub):
    client = mock()
    # Make the mock support context manager protocol
    when(client).__enter__().thenReturn(client)
    when(client).__exit__(None, None, None).thenReturn(None)

    when(quotas_logic).ClientWrapper(...).thenReturn(client)
    yield client
    unstub()


@pytest.fixture
def mock_quotas_api(mock_client_wrapper, unstub):
    api = mock()
    when(quotas_logic).QuotasApi(...).thenReturn(api)
    yield api
    unstub()


def test_get_user_quota(mock_quotas_api):
    pipeline_name = "Test Pipeline"
    mock_quota = QuotaWithDetails(
        pipeline_name=pipeline_name, quota_limit=1000, quota_consumed=300
    )
    when(mock_quotas_api).get_quota_for_pipeline(
        pipeline_name=pipeline_name
    ).thenReturn(mock_quota)

    result = quotas_logic.get_user_quota(pipeline_name)

    assert mock_quota.pipeline_name == result.pipeline_name
    assert mock_quota.quota_limit == result.quota_limit
    assert mock_quota.quota_consumed == result.quota_consumed
