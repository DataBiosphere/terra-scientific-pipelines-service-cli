# tests/commands/pipelines_tests.py

import logging
from click.testing import CliRunner
from mockito import when, verify
from terralab.commands import pipelines_commands
from teaspoons_client import (
    Pipeline,
    PipelineWithDetails,
    PipelineUserProvidedInputDefinition,
    ApiException,
)
from tests.utils_for_tests import capture_logs

LOGGER = logging.getLogger(__name__)


def test_list_pipelines(capture_logs):
    runner = CliRunner()
    test_pipelines = [
        Pipeline(
            pipeline_name="test_pipeline_1",
            display_name="test_display_name_1",
            description="test_description_1",
        ),
        Pipeline(
            pipeline_name="test_pipeline_2",
            display_name="test_display_name_2",
            description="test_description_2",
        ),
    ]

    when(pipelines_commands.pipelines_logic).list_pipelines().thenReturn(test_pipelines)

    result = runner.invoke(pipelines_commands.pipelines, ["list"])

    assert result.exit_code == 0
    verify(pipelines_commands.pipelines_logic).list_pipelines()
    assert "Found 2 available pipelines:" in capture_logs.text
    assert "test_pipeline_1" in capture_logs.text
    assert "test_pipeline_2" in capture_logs.text


def test_get_info_success(capture_logs, unstub):
    test_pipeline_name = "test_pipeline"
    test_input_definition = PipelineUserProvidedInputDefinition(
        name="test_input", type="test_type"
    )
    test_pipeline = PipelineWithDetails(
        pipeline_name=test_pipeline_name,
        description="test_description",
        display_name="test_display_name",
        type="test_type",
        inputs=[test_input_definition],
    )

    when(pipelines_commands.pipelines_logic).get_pipeline_info(
        test_pipeline_name
    ).thenReturn(test_pipeline)

    runner = CliRunner()
    result = runner.invoke(
        pipelines_commands.pipelines, ["get-info", test_pipeline_name]
    )

    assert result.exit_code == 0
    verify(pipelines_commands.pipelines_logic).get_pipeline_info(test_pipeline_name)
    assert test_pipeline_name in capture_logs.text
    assert "test_description" in capture_logs.text
    assert "test_input" in capture_logs.text

    unstub()


def test_get_info_missing_argument():
    runner = CliRunner()

    result = runner.invoke(pipelines_commands.pipelines, ["get-info"])

    assert result.exit_code != 0
    assert "Error: Missing argument 'PIPELINE_NAME'" in result.output


def test_get_info_api_exception(capture_logs, unstub):
    runner = CliRunner()

    when(pipelines_commands.pipelines_logic).get_pipeline_info(
        "bad_pipeline_name"
    ).thenRaise(
        ApiException(
            status=400,
            reason="Error Reason",
            body='{"message": "this is the body message"}',
        )
    )

    result = runner.invoke(
        pipelines_commands.pipelines, ["get-info", "bad_pipeline_name"]
    )

    assert result.exit_code != 0
    verify(pipelines_commands.pipelines_logic).get_pipeline_info("bad_pipeline_name")
    assert (
        "API call failed with status code 400 (Error Reason): this is the body message"
        in capture_logs.text
    )

    unstub()
