# tests/commands/test_quotas_commands.py

from click.testing import CliRunner
from mockito import when, verify
from teaspoons_client import QuotaWithDetails, ApiException

from terralab.commands import quotas_commands
from tests.utils_for_tests import capture_logs


def test_get_info_success(capture_logs, unstub):
    test_pipeline_name = "test_pipeline"
    test_quota_details = QuotaWithDetails(
        pipeline_name=test_pipeline_name, quota_limit=1000, quota_consumed=300
    )

    when(quotas_commands.quotas_logic).get_user_quota(test_pipeline_name).thenReturn(
        test_quota_details
    )

    runner = CliRunner()
    result = runner.invoke(quotas_commands.quota, [test_pipeline_name])

    assert result.exit_code == 0
    verify(quotas_commands.quotas_logic).get_user_quota(test_pipeline_name)
    assert (
        "Note: It may take a few minutes for recently submitted jobs to be reflected."
        in capture_logs.text
    )
    assert test_pipeline_name in capture_logs.text
    # quota limit
    assert "Quota Limit: 1000" in capture_logs.text
    # quota consumed
    assert "Quota Used: 300" in capture_logs.text
    # quota left
    assert "Quota Available: 700" in capture_logs.text

    unstub()


def test_get_info_missing_argument():
    runner = CliRunner()

    result = runner.invoke(quotas_commands.quota, [])

    assert result.exit_code != 0
    assert "Error: Missing argument 'PIPELINE_NAME'" in result.output


def test_get_info_api_exception(capture_logs, unstub):
    runner = CliRunner()

    when(quotas_commands.quotas_logic).get_user_quota("bad_pipeline_name").thenRaise(
        ApiException(
            status=400,
            reason="Error Reason",
            body='{"message": "this is the body message"}',
        )
    )

    result = runner.invoke(quotas_commands.quota, ["bad_pipeline_name"])

    assert result.exit_code != 0
    verify(quotas_commands.quotas_logic).get_user_quota("bad_pipeline_name")
    assert (
        "API call failed with status code 400 (Error Reason): this is the body message"
        in capture_logs.text
    )

    unstub()
