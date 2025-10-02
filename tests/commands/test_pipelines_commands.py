# tests/commands/test_pipelines_commands.py

import logging
import pytest

from click.testing import CliRunner
from mockito import when, verify
from teaspoons_client import (
    Pipeline,
    PipelineOutputDefinition,
    PipelineWithDetails,
    PipelineUserProvidedInputDefinition,
    ApiException,
    PipelineQuota,
)

from terralab.commands import pipelines_commands
from terralab.constants import SUPPORT_EMAIL_TEXT
from tests.conftest import capture_logs

LOGGER = logging.getLogger(__name__)

pytestmark = pytest.mark.usefixtures("unstub_fixture")


def test_list_pipelines(capture_logs):
    runner = CliRunner()
    test_pipelines = [
        Pipeline(
            pipeline_name="test_pipeline_1",
            pipeline_version=1,
            display_name="test_display_name_1",
            description="test_description_1",
        ),
        Pipeline(
            pipeline_name="test_pipeline_2",
            pipeline_version=2,
            display_name="test_display_name_2",
            description="test_description_2",
        ),
    ]

    when(pipelines_commands.pipelines_logic).list_pipelines().thenReturn(test_pipelines)

    result = runner.invoke(pipelines_commands.pipelines, ["list"])

    assert result.exit_code == 0
    verify(pipelines_commands.pipelines_logic).list_pipelines()
    assert "Found 2 available pipelines:" in capture_logs.text
    assert "Name" in capture_logs.text
    assert "Version" in capture_logs.text
    assert "Description" in capture_logs.text
    assert "test_pipeline_1" in capture_logs.text
    assert "test_pipeline_2" in capture_logs.text


def test_get_info_success_no_version(capture_logs):
    test_pipeline_name = "test_pipeline"
    test_input_definition = PipelineUserProvidedInputDefinition(
        name="test_input", type="test_type"
    )
    test_output_definition = PipelineOutputDefinition(
        name="test_output", type="test_type"
    )
    test_pipeline_quota = PipelineQuota(
        pipeline_name="test_pipeline",
        default_quota=1000,
        min_quota_consumed=500,
        quota_units="units",
    )
    test_pipeline = PipelineWithDetails(
        pipeline_name=test_pipeline_name,
        pipeline_version=1,
        description="test_description",
        display_name="test_display_name",
        type="test_type",
        inputs=[test_input_definition],
        outputs=[test_output_definition],
        pipeline_quota=test_pipeline_quota,
    )

    when(pipelines_commands.pipelines_logic).get_pipeline_info(
        test_pipeline_name, None
    ).thenReturn(test_pipeline)

    runner = CliRunner()
    result = runner.invoke(
        pipelines_commands.pipelines, ["details", test_pipeline_name]
    )

    assert result.exit_code == 0
    verify(pipelines_commands.pipelines_logic).get_pipeline_info(
        test_pipeline_name, None
    )
    assert test_pipeline_name in capture_logs.text
    assert "Pipeline Version:   1" in capture_logs.text
    assert "test_description" in capture_logs.text
    assert "test_input" in capture_logs.text
    assert "test_output" in capture_logs.text
    assert "Min Quota Consumed: 500 units" in capture_logs.text


def test_get_info_success_version(capture_logs):
    test_pipeline_name = "test_pipeline"
    test_input_definition = PipelineUserProvidedInputDefinition(
        name="test_input", type="test_type"
    )
    test_output_definition = PipelineOutputDefinition(
        name="test_output", type="test_type"
    )
    test_pipeline_quota = PipelineQuota(
        pipeline_name="test_pipeline",
        default_quota=1000,
        min_quota_consumed=500,
        quota_units="units",
    )
    test_pipeline = PipelineWithDetails(
        pipeline_name=test_pipeline_name,
        pipeline_version=1,
        description="test_description",
        display_name="test_display_name",
        type="test_type",
        inputs=[test_input_definition],
        outputs=[test_output_definition],
        pipeline_quota=test_pipeline_quota,
    )

    when(pipelines_commands.pipelines_logic).get_pipeline_info(
        test_pipeline_name, 1
    ).thenReturn(test_pipeline)

    runner = CliRunner()
    result = runner.invoke(
        pipelines_commands.pipelines, ["details", test_pipeline_name, "--version", 1]
    )

    assert result.exit_code == 0
    verify(pipelines_commands.pipelines_logic).get_pipeline_info(test_pipeline_name, 1)
    assert test_pipeline_name in capture_logs.text
    assert "Pipeline Version:   1" in capture_logs.text
    assert "test_description" in capture_logs.text
    assert "test_input" in capture_logs.text
    assert "test_output" in capture_logs.text
    assert "Min Quota Consumed: 500 units" in capture_logs.text


def test_get_info_missing_argument():
    runner = CliRunner()

    result = runner.invoke(pipelines_commands.pipelines, ["details"])

    assert result.exit_code != 0
    assert "Error: Missing argument 'PIPELINE_NAME'" in result.output


def test_get_info_api_exception(capture_logs):
    runner = CliRunner()

    when(pipelines_commands.pipelines_logic).get_pipeline_info(
        "bad_pipeline_name", None
    ).thenRaise(
        ApiException(
            status=400,
            reason="Error Reason",
            body='{"message": "this is the body message"}',
        )
    )

    result = runner.invoke(
        pipelines_commands.pipelines, ["details", "bad_pipeline_name"]
    )

    assert result.exit_code != 0
    verify(pipelines_commands.pipelines_logic).get_pipeline_info(
        "bad_pipeline_name", None
    )
    assert (
        "API call failed with status code 400 (Error Reason): this is the body message"
        in capture_logs.text
    )
    assert SUPPORT_EMAIL_TEXT in capture_logs.text


def test_get_info_api_exception_no_body(capture_logs):
    runner = CliRunner()

    when(pipelines_commands.pipelines_logic).get_pipeline_info(
        "bad_pipeline_name", None
    ).thenRaise(
        ApiException(
            status=400,
            reason="Error Reason",
        )
    )

    result = runner.invoke(
        pipelines_commands.pipelines, ["details", "bad_pipeline_name"]
    )

    assert result.exit_code != 0
    verify(pipelines_commands.pipelines_logic).get_pipeline_info(
        "bad_pipeline_name", None
    )
    assert "API call failed with status code 400 (Error Reason)" in capture_logs.text
    assert SUPPORT_EMAIL_TEXT in capture_logs.text


def test_get_info_api_exception_401_no_user_found(capture_logs):
    runner = CliRunner()
    pipeline_name = "whatever"

    when(pipelines_commands.pipelines_logic).get_pipeline_info(
        pipeline_name, None
    ).thenRaise(
        ApiException(
            status=401,
            reason=None,
            body='{"message": "User not found"}',
        )
    )

    result = runner.invoke(pipelines_commands.pipelines, ["details", pipeline_name])

    assert result.exit_code != 0
    verify(pipelines_commands.pipelines_logic).get_pipeline_info(pipeline_name, None)
    assert (
        "User not found in Terra. Are you sure you've registered? Visit https://services.terra.bio to register."
        in capture_logs.text
    )


def test_get_info_api_exception_401_unauthorized(capture_logs):
    runner = CliRunner()
    pipeline_name = "whatever"

    when(pipelines_commands.pipelines_logic).get_pipeline_info(
        pipeline_name, None
    ).thenRaise(
        ApiException(
            status=401,
            reason="Unauthorized",
            body="""<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>401 Unauthorized</title>
</head><body>
<h1>Unauthorized</h1>
<p>This server could not verify that you
are authorized to access the document
requested.  Either you supplied the wrong
credentials (e.g., bad password), or your
browser doesn't understand how to supply
the credentials required.</p>
</body></html>""",
        )
    )

    result = runner.invoke(pipelines_commands.pipelines, ["details", pipeline_name])

    assert result.exit_code != 0
    verify(pipelines_commands.pipelines_logic).get_pipeline_info(pipeline_name, None)
    assert (
        "Something went wrong with authorization. Please run 'terralab logout' and then try again."
        in capture_logs.text
    )


def test_get_info_api_exception_different_401(capture_logs):
    runner = CliRunner()
    pipeline_name = "whatever"

    when(pipelines_commands.pipelines_logic).get_pipeline_info(
        pipeline_name, None
    ).thenRaise(
        ApiException(
            status=401,
            reason="Error Reason",
            body='{"message": "Something other than user not found"}',
        )
    )

    result = runner.invoke(pipelines_commands.pipelines, ["details", pipeline_name])

    assert result.exit_code != 0
    verify(pipelines_commands.pipelines_logic).get_pipeline_info(pipeline_name, None)
    assert (
        "API call failed with status code 401 (Error Reason): Something other than user not found"
        in capture_logs.text
    )
    assert SUPPORT_EMAIL_TEXT in capture_logs.text


def test_non_json_api_exception_body(capture_logs):
    runner = CliRunner()
    pipeline_name = "whatever"

    when(pipelines_commands.pipelines_logic).get_pipeline_info(
        pipeline_name, None
    ).thenRaise(
        ApiException(
            status=403,
            reason=None,
            body="403 Forbidden: blah blah blah",
        )
    )

    result = runner.invoke(pipelines_commands.pipelines, ["details", pipeline_name])

    assert result.exit_code != 0
    verify(pipelines_commands.pipelines_logic).get_pipeline_info(pipeline_name, None)
    assert "403 Forbidden: blah blah blah" in capture_logs.text
