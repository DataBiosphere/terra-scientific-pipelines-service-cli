# tests/commands/test_pipeline_runs_commands.py

import logging
import pytest
import uuid
from click.testing import CliRunner
from mockito import when, verify, mock

from teaspoons_client import (
    AsyncPipelineRunResponse,
    JobReport,
    ErrorReport,
    PipelineRunReport,
)
from terralab.constants import SUPPORT_EMAIL_TEXT, SUCCEEDED_KEY, FAILED_KEY
from terralab.commands import pipeline_runs_commands
from tests.utils_for_tests import capture_logs

LOGGER = logging.getLogger(__name__)

# common constants for tests
TEST_PIPELINE_NAME = "test_pipeline"
TEST_INPUT_KEY = "--foo_key"
TEST_INPUT_VALUE = "foo_value"
TEST_INPUTS_TUPLE = (TEST_INPUT_KEY, TEST_INPUT_VALUE)
TEST_INPUTS_DICT = {TEST_INPUT_KEY.lstrip("--"): TEST_INPUT_VALUE}
TEST_DESCRIPTION = "user description"
TEST_JOB_ID = uuid.uuid4()


def test_submit(capture_logs):
    runner = CliRunner()

    when(pipeline_runs_commands).process_inputs_to_dict(TEST_INPUTS_TUPLE).thenReturn(
        TEST_INPUTS_DICT
    )
    when(pipeline_runs_commands.pipelines_logic).validate_pipeline_inputs(
        TEST_PIPELINE_NAME, None, TEST_INPUTS_DICT
    )  # do nothing

    when(pipeline_runs_commands.pipeline_runs_logic).prepare_upload_start_pipeline_run(
        TEST_PIPELINE_NAME, None, TEST_INPUTS_DICT, TEST_DESCRIPTION
    ).thenReturn(TEST_JOB_ID)

    result = runner.invoke(
        pipeline_runs_commands.submit,
        [
            TEST_PIPELINE_NAME,
            TEST_INPUT_KEY,
            TEST_INPUT_VALUE,
            "--description",
            TEST_DESCRIPTION,
        ],
    )

    assert result.exit_code == 0
    assert (
        f"Successfully started {TEST_PIPELINE_NAME} job {TEST_JOB_ID}"
        in capture_logs.text
    )


def test_submit_no_description(capture_logs):
    runner = CliRunner()

    TEST_JOB_ID = uuid.uuid4()

    when(pipeline_runs_commands).process_inputs_to_dict(TEST_INPUTS_TUPLE).thenReturn(
        TEST_INPUTS_DICT
    )
    when(pipeline_runs_commands.pipelines_logic).validate_pipeline_inputs(
        TEST_PIPELINE_NAME, None, TEST_INPUTS_DICT
    )  # do nothing

    when(pipeline_runs_commands.pipeline_runs_logic).prepare_upload_start_pipeline_run(
        TEST_PIPELINE_NAME, None, TEST_INPUTS_DICT, ""
    ).thenReturn(TEST_JOB_ID)

    result = runner.invoke(
        pipeline_runs_commands.submit,
        [TEST_PIPELINE_NAME, TEST_INPUT_KEY, TEST_INPUT_VALUE],
    )

    assert result.exit_code == 0
    assert (
        f"Successfully started {TEST_PIPELINE_NAME} job {TEST_JOB_ID}"
        in capture_logs.text
    )


def test_submit_with_version(capture_logs):
    runner = CliRunner()

    when(pipeline_runs_commands).process_inputs_to_dict(TEST_INPUTS_TUPLE).thenReturn(
        TEST_INPUTS_DICT
    )
    when(pipeline_runs_commands.pipelines_logic).validate_pipeline_inputs(
        TEST_PIPELINE_NAME, 1, TEST_INPUTS_DICT
    )  # do nothing

    when(pipeline_runs_commands.pipeline_runs_logic).prepare_upload_start_pipeline_run(
        TEST_PIPELINE_NAME, 1, TEST_INPUTS_DICT, ""
    ).thenReturn(TEST_JOB_ID)

    result = runner.invoke(
        pipeline_runs_commands.submit,
        [TEST_PIPELINE_NAME, TEST_INPUT_KEY, TEST_INPUT_VALUE, "--version", "1"],
    )

    assert result.exit_code == 0
    assert (
        f"Successfully started {TEST_PIPELINE_NAME} job {TEST_JOB_ID}"
        in capture_logs.text
    )


def test_download():
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)

    when(
        pipeline_runs_commands.pipeline_runs_logic
    ).get_result_and_download_pipeline_run_outputs(
        TEST_JOB_ID, "."
    )  # do nothing, assume succeeded

    result = runner.invoke(pipeline_runs_commands.download, [test_job_id_str])

    assert result.exit_code == 0
    verify(
        pipeline_runs_commands.pipeline_runs_logic
    ).get_result_and_download_pipeline_run_outputs(TEST_JOB_ID, ".")


def test_download_bad_job_id(capture_logs):
    runner = CliRunner()

    test_job_id_str = "not a uuid"

    result = runner.invoke(pipeline_runs_commands.download, [test_job_id_str])

    assert result.exit_code == 1
    assert "Error: JOB_ID must be a valid uuid." in capture_logs.text


def test_details_running_job(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)

    test_response = create_test_pipeline_run_response(
        TEST_PIPELINE_NAME, test_job_id_str, "RUNNING"
    )

    when(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_run_status(
        TEST_JOB_ID
    ).thenReturn(test_response)

    result = runner.invoke(pipeline_runs_commands.jobs, ["details", test_job_id_str])

    assert result.exit_code == 0
    verify(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_run_status(
        TEST_JOB_ID
    )
    assert "Status:" in capture_logs.text
    assert "Completed:" not in capture_logs.text

    unstub()


def test_details_succeeded_job(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)

    test_response = create_test_pipeline_run_response(
        TEST_PIPELINE_NAME, test_job_id_str, SUCCEEDED_KEY
    )

    when(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_run_status(
        TEST_JOB_ID
    ).thenReturn(test_response)

    result = runner.invoke(pipeline_runs_commands.jobs, ["details", test_job_id_str])

    assert result.exit_code == 0
    verify(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_run_status(
        TEST_JOB_ID
    )
    assert "Status:" in capture_logs.text
    assert "Completed:" in capture_logs.text
    assert "File Download Expiration:" in capture_logs.text

    unstub()


def test_details_failed_job(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)
    test_error_message = "Something went wrong"

    test_response = create_test_pipeline_run_response(
        TEST_PIPELINE_NAME,
        test_job_id_str,
        FAILED_KEY,
        error_message=test_error_message,
    )

    when(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_run_status(
        TEST_JOB_ID
    ).thenReturn(test_response)

    result = runner.invoke(pipeline_runs_commands.jobs, ["details", test_job_id_str])

    assert result.exit_code == 0
    assert "Status:" in capture_logs.text
    assert test_error_message in capture_logs.text
    assert SUPPORT_EMAIL_TEXT in capture_logs.text
    assert "Completed:" in capture_logs.text

    unstub()


def test_details_bad_job_id(capture_logs):
    runner = CliRunner()

    test_job_id_str = "not a uuid"

    result = runner.invoke(pipeline_runs_commands.jobs, ["details", test_job_id_str])

    assert result.exit_code == 1
    assert "Error: JOB_ID must be a valid uuid." in capture_logs.text


def test_list_jobs(capture_logs):
    runner = CliRunner()

    test_pipeline_runs = [
        mock(
            {
                "job_id": str(uuid.uuid4()),
                "pipeline_name": "test_pipeline1",
                "status": SUCCEEDED_KEY,
                "time_submitted": "2024-01-01T12:00:00Z",
                "time_completed": "2024-01-01T12:30:00Z",
                "description": "test description 1",
            }
        ),
        mock(
            {
                "job_id": str(uuid.uuid4()),
                "pipeline_name": "test_pipeline2",
                "status": FAILED_KEY,
                "time_submitted": "2024-01-02T12:00:00Z",
                "time_completed": "2024-01-02T12:30:00Z",
                "description": "test description 2",
            }
        ),
    ]

    when(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_runs(10).thenReturn(
        test_pipeline_runs
    )

    result = runner.invoke(pipeline_runs_commands.jobs, ["list"])

    assert result.exit_code == 0
    # Check that job details are in output
    assert test_pipeline_runs[0].job_id in capture_logs.text
    assert test_pipeline_runs[0].pipeline_name in capture_logs.text
    assert "Succeeded" in capture_logs.text
    assert test_pipeline_runs[1].job_id in capture_logs.text
    assert test_pipeline_runs[1].pipeline_name in capture_logs.text
    assert "Failed" in capture_logs.text


def test_list_jobs_custom_limit(capture_logs):
    runner = CliRunner()
    test_n_results = 5

    test_pipeline_runs = [
        mock(
            {
                "job_id": str(uuid.uuid4()),
                "status": SUCCEEDED_KEY,
                "pipeline_name": "test_pipeline",
                "time_submitted": "2024-01-01T12:00:00Z",
                "time_completed": "2024-01-01T12:30:00Z",
                "description": "test description",
            }
        )
    ]

    when(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_runs(
        test_n_results
    ).thenReturn(test_pipeline_runs)

    result = runner.invoke(
        pipeline_runs_commands.jobs, ["list", "--num_results", test_n_results]
    )

    assert result.exit_code == 0
    assert test_pipeline_runs[0].job_id in capture_logs.text


def test_list_jobs_no_results(capture_logs):
    runner = CliRunner()

    when(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_runs(10).thenReturn(
        []
    )

    result = runner.invoke(pipeline_runs_commands.jobs, ["list"])

    assert result.exit_code == 0


def create_test_pipeline_run_response(
    pipeline_name: str, job_id: str, status: str, error_message: str = None
):
    """Helper function for creating AsyncPipelineRunResponse objects used in tests"""
    status_code = 200
    if status == "RUNNING":
        status_code = 202
    error_report = None
    if error_message:
        error_report = ErrorReport(message=error_message, statusCode=500, causes=[])
    job_report = JobReport(
        id=job_id,
        statusCode=status_code,
        resultURL="foobar",
        status=status,
        submitted="2024-01-01T12:00:00Z",
        description="test description",
    )
    if status in [SUCCEEDED_KEY, FAILED_KEY]:
        job_report.completed = "2024-01-01T15:00:00Z"
    return AsyncPipelineRunResponse(
        jobReport=job_report,
        pipelineRunReport=PipelineRunReport(
            pipelineName=pipeline_name, pipelineVersion=1, wdlMethodVersion="1.0.0"
        ),
        errorReport=error_report,
    )
