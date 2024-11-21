# tests/commands/test_service_commands.py

import logging
from click.testing import CliRunner
from mockito import when, verify
from terralab.commands import service_commands
from teaspoons_client import (
    ApiException,
    VersionProperties
)
from tests.utils_for_tests import capture_logs

LOGGER = logging.getLogger(__name__)


def test_service_version(capture_logs, unstub):
    runner = CliRunner()

    test_git_tag = "0.0.0"
    test_git_hash = "12345"
    test_build = "0.0.0-SNAPSHOT"
    test_version_info = VersionProperties(
        gitTag=test_git_tag,
        gitHash=test_git_hash,
        build=test_build
    )

    when(service_commands.service_logic).get_version().thenReturn(test_version_info)

    result = runner.invoke(service_commands.service, ["version"])

    assert result.exit_code == 0
    verify(service_commands.service_logic).get_version()
    assert "Teaspoons service version information:" in capture_logs.text
    assert f"Git tag: {test_git_tag}" in capture_logs.text
    assert f"Git hash: {test_git_hash}" in capture_logs.text
    assert f"Build: {test_build}" in capture_logs.text

    unstub()


def test_service_version_api_exception(capture_logs, unstub):
    runner = CliRunner()
    
    when(service_commands.service_logic).get_version().thenRaise(ApiException(
            status=400,
            reason="Error Reason",
            body='{"message": "this is the body message"}',
        ))

    result = runner.invoke(service_commands.service, ["version"])

    assert result.exit_code != 0
    verify(service_commands.service_logic).get_version()
    assert (
        "API call failed with status code 400 (Error Reason): this is the body message"
        in capture_logs.text
    )

    unstub()


def test_service_status(capture_logs, unstub):
    runner = CliRunner()

    test_status = "Running"

    when(service_commands.service_logic).get_status().thenReturn(test_status)

    result = runner.invoke(service_commands.service, ["status"])

    assert result.exit_code == 0
    verify(service_commands.service_logic).get_status()
    assert test_status in capture_logs.text

    unstub()

def test_service_status_api_exception(capture_logs, unstub):
    runner = CliRunner()
    
    when(service_commands.service_logic).get_status().thenRaise(ApiException(
            status=400,
            reason="Error Reason",
            body='{"message": "this is the body message"}',
        ))

    result = runner.invoke(service_commands.service, ["status"])

    assert result.exit_code != 0
    verify(service_commands.service_logic).get_status()
    assert (
        "API call failed with status code 400 (Error Reason): this is the body message"
        in capture_logs.text
    )

    unstub()
