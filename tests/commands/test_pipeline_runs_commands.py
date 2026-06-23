# tests/commands/test_pipeline_runs_commands.py

import logging
import uuid

import pytest
from click.testing import CliRunner
from mockito import when, verify, mock
from teaspoons_client import (
    AsyncPipelineRunResponseV2,
    DataDeliveryReport,
    JobReport,
    ErrorReport,
    PipelineOutputDefinition,
    PipelineQuota,
    PipelineRunReportV2,
    PipelineUserProvidedInputDefinition,
    PipelineWithDetails,
)

from terralab.commands import pipeline_runs_commands
from terralab.constants import (
    SUPPORT_EMAIL_TEXT,
    SUCCEEDED_KEY,
    FAILED_KEY,
)
from terralab.utils import format_timestamp
from tests.conftest import capture_logs

LOGGER = logging.getLogger(__name__)

# common constants for tests
TEST_PIPELINE_NAME = "test_pipeline"
TEST_INPUT_KEY = "--foo_key"
TEST_INPUT_KEY_STRIPPED = TEST_INPUT_KEY.lstrip("--")
TEST_INPUT_VALUE = "foo_value"
TEST_INPUTS_TUPLE = (TEST_INPUT_KEY, TEST_INPUT_VALUE)
TEST_INPUTS_DICT = {TEST_INPUT_KEY_STRIPPED: TEST_INPUT_VALUE}
TEST_DESCRIPTION = "user description"
TEST_JOB_ID = uuid.uuid4()
TEST_QUOTA_CONSUMED = 500
TEST_INPUT_SIZE = 100
TEST_INPUT_UNIT = "samples"
OPTIONAL_INPUT_NAME = "optional_input"
OPTIONAL_INPUT_DEFAULT = "default_value"
TEST_PIPELINE_VERSION = 1


def test_submit(capture_logs):
    runner = CliRunner()

    when(pipeline_runs_commands).process_inputs_to_dict(TEST_INPUTS_TUPLE).thenReturn(
        TEST_INPUTS_DICT
    )
    when(pipeline_runs_commands.pipelines_logic).validate_pipeline_inputs(
        TEST_PIPELINE_NAME, None, TEST_INPUTS_DICT
    )  # do nothing

    when(pipeline_runs_commands.pipeline_runs_logic).prepare_upload_start_pipeline_run(
        TEST_PIPELINE_NAME, None, TEST_INPUTS_DICT, TEST_DESCRIPTION, True
    ).thenReturn(TEST_JOB_ID)

    result = runner.invoke(
        pipeline_runs_commands.submit,
        [
            TEST_PIPELINE_NAME,
            TEST_INPUT_KEY,
            TEST_INPUT_VALUE,
            "--description",
            TEST_DESCRIPTION,
            "--agreeToTerms",
        ],
    )

    assert result.exit_code == 0
    assert (
        f"Successfully started {TEST_PIPELINE_NAME} job {TEST_JOB_ID}"
        in capture_logs.text
    )


def test_submit_with_prompt_to_agree_to_terms(capture_logs):
    runner = CliRunner()

    result = runner.invoke(
        pipeline_runs_commands.submit,
        [
            TEST_PIPELINE_NAME,
            TEST_INPUT_KEY,
            TEST_INPUT_VALUE,
            "--description",
            TEST_DESCRIPTION,
        ],
        input="y\n",  # simulate user entering 'y' at the prompt
    )

    assert result.exit_code == 0
    assert (
        f"Successfully started {TEST_PIPELINE_NAME} job {TEST_JOB_ID}"
        in capture_logs.text
    )


def test_submit_no_agree_to_terms(capture_logs):
    runner = CliRunner()

    result = runner.invoke(
        pipeline_runs_commands.submit,
        [
            TEST_PIPELINE_NAME,
            TEST_INPUT_KEY,
            TEST_INPUT_VALUE,
            "--description",
            TEST_DESCRIPTION,
        ],
        input="n\n",  # simulate user entering 'n' at the prompt
    )

    assert result.exit_code == 1
    assert (
        "You must agree to the terms of service to run a pipeline" in capture_logs.text
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
        TEST_PIPELINE_NAME, None, TEST_INPUTS_DICT, "", True
    ).thenReturn(TEST_JOB_ID)

    result = runner.invoke(
        pipeline_runs_commands.submit,
        [TEST_PIPELINE_NAME, TEST_INPUT_KEY, TEST_INPUT_VALUE, "--agreeToTerms"],
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
        TEST_PIPELINE_NAME, 1, TEST_INPUTS_DICT, "", True
    ).thenReturn(TEST_JOB_ID)

    result = runner.invoke(
        pipeline_runs_commands.submit,
        [
            TEST_PIPELINE_NAME,
            TEST_INPUT_KEY,
            TEST_INPUT_VALUE,
            "--version",
            "1",
            "--agreeToTerms",
        ],
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
    ).get_signed_urls_and_download_pipeline_run_outputs(
        TEST_JOB_ID, "."
    )  # do nothing, assume succeeded

    result = runner.invoke(pipeline_runs_commands.download, [test_job_id_str])

    assert result.exit_code == 0
    verify(
        pipeline_runs_commands.pipeline_runs_logic
    ).get_signed_urls_and_download_pipeline_run_outputs(TEST_JOB_ID, ".")


def test_download_bad_job_id(capture_logs):
    runner = CliRunner()

    test_job_id_str = "not a uuid"

    result = runner.invoke(pipeline_runs_commands.download, [test_job_id_str])

    assert result.exit_code == 1
    assert "Error: JOB_ID must be a valid uuid." in capture_logs.text


def test_deliver(capture_logs):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)
    test_destination = "gs://my-bucket/my-destination"

    when(pipeline_runs_commands.pipeline_runs_logic).deliver_pipeline_run_to_cloud(
        TEST_JOB_ID, test_destination
    )  # do nothing

    result = runner.invoke(
        pipeline_runs_commands.deliver, [test_job_id_str, test_destination]
    )

    assert result.exit_code == 0
    assert (
        f"Successfully initiated data delivery for job {test_job_id_str} to {test_destination}"
        in capture_logs.text
    )
    assert (
        f"You can check the status of the delivery with `terralab jobs details {test_job_id_str}`"
        in capture_logs.text
    )
    verify(pipeline_runs_commands.pipeline_runs_logic).deliver_pipeline_run_to_cloud(
        TEST_JOB_ID, test_destination
    )


def test_deliver_bad_job_id(capture_logs):
    runner = CliRunner()

    result = runner.invoke(
        pipeline_runs_commands.deliver,
        ["not a uuid", "gs://my-bucket/destination"],
    )

    assert result.exit_code == 1
    assert "Error: JOB_ID must be a valid uuid." in capture_logs.text


def test_deliver_bad_destination(capture_logs):
    runner = CliRunner()

    result = runner.invoke(
        pipeline_runs_commands.deliver, [str(TEST_JOB_ID), "not-a-gcs-path"]
    )

    assert result.exit_code == 1
    assert "Error: 'not-a-gcs-path' is not a valid GCS path" in capture_logs.text


def test_deliver_api_error(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)
    test_destination = "gs://my-bucket/my-destination"

    when(pipeline_runs_commands.pipeline_runs_logic).deliver_pipeline_run_to_cloud(
        TEST_JOB_ID, test_destination
    ).thenRaise(Exception("API error"))

    result = runner.invoke(
        pipeline_runs_commands.deliver, [test_job_id_str, test_destination]
    )

    assert result.exit_code == 1
    assert "API error" in capture_logs.text

    unstub()


def test_download_api_error(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)

    when(
        pipeline_runs_commands.pipeline_runs_logic
    ).get_signed_urls_and_download_pipeline_run_outputs(TEST_JOB_ID, ".").thenRaise(
        Exception("API error")
    )

    result = runner.invoke(pipeline_runs_commands.download, [test_job_id_str])

    assert result.exit_code == 1
    assert "API error" in capture_logs.text

    unstub()


def test_details_running_job(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)
    user_defined_optional_input_value = "user_value"
    test_inputs_dict_with_optional = {
        TEST_INPUT_KEY.lstrip("--"): TEST_INPUT_VALUE,
        OPTIONAL_INPUT_NAME: user_defined_optional_input_value,
    }

    test_response = create_test_pipeline_run_response(
        TEST_PIPELINE_NAME, test_job_id_str, "RUNNING", include_input_size=True
    )
    test_response.pipeline_run_report.user_inputs = test_inputs_dict_with_optional

    when(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_run_status(
        TEST_JOB_ID
    ).thenReturn(test_response)

    test_pipeline = create_test_pipeline_with_inputs()
    when(pipeline_runs_commands.pipelines_logic).get_pipeline_info(
        TEST_PIPELINE_NAME, TEST_PIPELINE_VERSION
    ).thenReturn(test_pipeline)

    result = runner.invoke(pipeline_runs_commands.jobs, ["details", test_job_id_str])

    assert result.exit_code == 0
    verify(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_run_status(
        TEST_JOB_ID
    )
    assert "Status:" in capture_logs.text
    assert "Completed:" not in capture_logs.text
    assert f"Input size: {TEST_INPUT_SIZE} {TEST_INPUT_UNIT}" in capture_logs.text
    assert "Inputs:" in capture_logs.text
    assert f"{TEST_INPUT_KEY_STRIPPED}:" in capture_logs.text
    assert TEST_INPUT_VALUE in capture_logs.text
    assert f"{OPTIONAL_INPUT_NAME}:" in capture_logs.text
    assert user_defined_optional_input_value in capture_logs.text
    unstub()


def test_details_running_job_with_input_size(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)

    test_response = create_test_pipeline_run_response(
        TEST_PIPELINE_NAME, test_job_id_str, "RUNNING", include_input_size=True
    )

    when(pipeline_runs_commands.pipelines_logic).get_pipeline_info(
        TEST_PIPELINE_NAME, TEST_PIPELINE_VERSION
    ).thenReturn(create_test_pipeline_with_inputs())
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
    assert f"Input size: {TEST_INPUT_SIZE} {TEST_INPUT_UNIT}" in capture_logs.text
    assert "Inputs:" in capture_logs.text
    assert f"{TEST_INPUT_KEY_STRIPPED}:" in capture_logs.text
    assert TEST_INPUT_VALUE in capture_logs.text

    unstub()


def test_details_running_job_without_input_size(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)

    test_response = create_test_pipeline_run_response(
        TEST_PIPELINE_NAME, test_job_id_str, "RUNNING", include_input_size=False
    )

    when(pipeline_runs_commands.pipelines_logic).get_pipeline_info(
        TEST_PIPELINE_NAME, TEST_PIPELINE_VERSION
    ).thenReturn(create_test_pipeline_with_inputs())
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
    assert f"Input size: {TEST_INPUT_SIZE} {TEST_INPUT_UNIT}" not in capture_logs.text
    assert "Inputs:" in capture_logs.text
    assert f"{TEST_INPUT_KEY_STRIPPED}:" in capture_logs.text
    assert TEST_INPUT_VALUE in capture_logs.text

    unstub()


def test_details_succeeded_job(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)

    test_response = create_test_pipeline_run_response(
        TEST_PIPELINE_NAME, test_job_id_str, SUCCEEDED_KEY, include_input_size=True
    )

    when(pipeline_runs_commands.pipelines_logic).get_pipeline_info(
        TEST_PIPELINE_NAME, TEST_PIPELINE_VERSION
    ).thenReturn(create_test_pipeline_with_inputs())
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
    assert f"Quota Consumed: {TEST_QUOTA_CONSUMED}" in capture_logs.text
    assert f"Input size: {TEST_INPUT_SIZE} {TEST_INPUT_UNIT}" in capture_logs.text
    assert "Inputs:" in capture_logs.text
    assert f"{TEST_INPUT_KEY_STRIPPED}:" in capture_logs.text
    assert TEST_INPUT_VALUE in capture_logs.text
    assert "Outputs:" in capture_logs.text
    assert "output1:" in capture_logs.text
    assert (
        "gs://bucket/path/to/output1 (1.0 MiB)" in capture_logs.text
    )  # input size is 1048576 bytes
    assert "output2:" in capture_logs.text
    assert "gs://bucket/path/to/output2" in capture_logs.text
    assert "Data Delivery:" not in capture_logs.text

    unstub()


def test_details_succeeded_job_with_delivery(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)
    test_delivery_destination = "gs://my-bucket/my-destination"

    test_response = create_test_pipeline_run_response(
        TEST_PIPELINE_NAME,
        test_job_id_str,
        SUCCEEDED_KEY,
        include_input_size=True,
        delivery_status=SUCCEEDED_KEY,
        delivery_destination=test_delivery_destination,
    )

    when(pipeline_runs_commands.pipelines_logic).get_pipeline_info(
        TEST_PIPELINE_NAME, TEST_PIPELINE_VERSION
    ).thenReturn(create_test_pipeline_with_inputs())
    when(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_run_status(
        TEST_JOB_ID
    ).thenReturn(test_response)

    result = runner.invoke(pipeline_runs_commands.jobs, ["details", test_job_id_str])

    assert result.exit_code == 0
    assert "Data Delivery:" in capture_logs.text
    assert "Status: Succeeded" in capture_logs.text
    assert f"Destination: {test_delivery_destination}" in capture_logs.text

    unstub()


def test_details_failed_job_with_input_size(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)
    test_error_message = "Something went wrong"

    when(pipeline_runs_commands.pipelines_logic).get_pipeline_info(
        TEST_PIPELINE_NAME, TEST_PIPELINE_VERSION
    ).thenReturn(create_test_pipeline_with_inputs())
    test_response = create_test_pipeline_run_response(
        TEST_PIPELINE_NAME,
        test_job_id_str,
        FAILED_KEY,
        include_input_size=True,
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
    assert "Quota Consumed: 0" in capture_logs.text
    assert f"Input size: {TEST_INPUT_SIZE} {TEST_INPUT_UNIT}" in capture_logs.text
    assert "Inputs:" in capture_logs.text
    assert f"{TEST_INPUT_KEY_STRIPPED}:" in capture_logs.text
    assert TEST_INPUT_VALUE in capture_logs.text

    unstub()


def test_details_failed_job_without_input_size(capture_logs, unstub):
    runner = CliRunner()

    test_job_id_str = str(TEST_JOB_ID)
    test_error_message = "Something went wrong"

    test_response = create_test_pipeline_run_response(
        TEST_PIPELINE_NAME,
        test_job_id_str,
        FAILED_KEY,
        include_input_size=False,
        error_message=test_error_message,
    )

    when(pipeline_runs_commands.pipelines_logic).get_pipeline_info(
        TEST_PIPELINE_NAME, TEST_PIPELINE_VERSION
    ).thenReturn(create_test_pipeline_with_inputs())
    when(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_run_status(
        TEST_JOB_ID
    ).thenReturn(test_response)

    result = runner.invoke(pipeline_runs_commands.jobs, ["details", test_job_id_str])

    assert result.exit_code == 0
    assert "Status:" in capture_logs.text
    assert test_error_message in capture_logs.text
    assert SUPPORT_EMAIL_TEXT in capture_logs.text
    assert "Completed:" in capture_logs.text
    assert "Quota Consumed: 0" in capture_logs.text
    assert f"Input size: {TEST_INPUT_SIZE} {TEST_INPUT_UNIT}" not in capture_logs.text
    assert "Inputs:" in capture_logs.text
    assert f"{TEST_INPUT_KEY_STRIPPED}:" in capture_logs.text
    assert TEST_INPUT_VALUE in capture_logs.text

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
                "pipeline_version": 1234567,
                "status": SUCCEEDED_KEY,
                "time_submitted": "2024-01-01T12:00:00Z",
                "time_completed": "2024-01-01T12:30:00Z",
                "description": "test description 1",
                "quota_consumed": 127911,
                "output_expiration_date": "2024-01-15T12:30:00Z",
            }
        ),
        mock(
            {
                "job_id": str(uuid.uuid4()),
                "pipeline_name": "test_pipeline2",
                "pipeline_version": 111111111,
                "status": FAILED_KEY,
                "time_submitted": "2024-01-02T12:00:00Z",
                "time_completed": "2024-01-02T12:30:00Z",
                "description": "test description 2",
                "output_expiration_date": None,
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
    assert (
        f"{test_pipeline_runs[0].pipeline_name} v{test_pipeline_runs[0].pipeline_version}"
        in capture_logs.text
    )
    assert "Succeeded" in capture_logs.text
    assert (
        str(format_timestamp(test_pipeline_runs[0].output_expiration_date))
        in capture_logs.text
    )

    assert test_pipeline_runs[1].job_id in capture_logs.text
    assert (
        f"{test_pipeline_runs[1].pipeline_name} v{test_pipeline_runs[1].pipeline_version}"
        in capture_logs.text
    )
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
                "output_expiration_date": "2024-01-05T12:30:00Z",
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


def test_list_jobs_no_results():
    runner = CliRunner()

    when(pipeline_runs_commands.pipeline_runs_logic).get_pipeline_runs(10).thenReturn(
        []
    )

    result = runner.invoke(pipeline_runs_commands.jobs, ["list"])

    assert result.exit_code == 0


def test_list_jobs_request_exceeds_limit():
    runner = CliRunner()
    test_n_results = 150  # exceeds max of 100

    result = runner.invoke(
        pipeline_runs_commands.jobs, ["list", "--num_results", test_n_results]
    )

    assert result.exit_code != 0
    assert "Error: Invalid value for '--num_results'" in result.output


def test_list_jobs_request_too_low():
    runner = CliRunner()
    test_n_results = 0  # below min of 1

    result = runner.invoke(
        pipeline_runs_commands.jobs, ["list", "--num_results", test_n_results]
    )

    assert result.exit_code != 0
    assert "Error: Invalid value for '--num_results'" in result.output


def create_test_pipeline_run_response(
    pipeline_name: str,
    job_id: str,
    status: str,
    include_input_size: bool = False,
    error_message: str = None,
    delivery_status: str = None,
    delivery_destination: str = None,
) -> AsyncPipelineRunResponseV2:
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

    pipeline_run_report = PipelineRunReportV2(
        pipelineName=pipeline_name,
        pipelineVersion=TEST_PIPELINE_VERSION,
        toolVersion="1.0.0",
        user_inputs=TEST_INPUTS_DICT,
    )
    if status == SUCCEEDED_KEY:
        pipeline_run_report.outputs = {
            "output1": {
                "value": "gs://bucket/path/to/output1",
                "metadata": {"sizeInBytes": 1048576},
            },
            "output2": {"value": "gs://bucket/path/to/output2"},
        }
        pipeline_run_report.quota_consumed = TEST_QUOTA_CONSUMED

    if include_input_size:
        pipeline_run_report.input_size = TEST_INPUT_SIZE
        pipeline_run_report.input_size_units = TEST_INPUT_UNIT

    if delivery_status and delivery_destination:
        pipeline_run_report.data_delivery_report = DataDeliveryReport(
            destination=delivery_destination, status=delivery_status
        )

    return AsyncPipelineRunResponseV2(
        jobReport=job_report,
        pipelineRunReport=pipeline_run_report,
        errorReport=error_report,
    )


def create_test_pipeline_with_inputs() -> PipelineWithDetails:
    """Helper function for creating PipelineWithDetails objects used in tests"""
    test_pipeline_name = TEST_PIPELINE_NAME
    test_input_definition = PipelineUserProvidedInputDefinition(
        name=TEST_INPUT_KEY.lstrip("--"),
        displayName="Test Input",
        type="test_type",
        description="test input description",
        isRequired=True,
    )
    test_input_definition_optional = PipelineUserProvidedInputDefinition(
        name=OPTIONAL_INPUT_NAME,
        displayName="Optional Input",
        type="test_type",
        description="optional input description",
        defaultValue=OPTIONAL_INPUT_DEFAULT,
        isRequired=False,
    )
    test_output_definition = PipelineOutputDefinition(
        name="test_output",
        displayName="Test Output",
        type="test_type",
        description="test output description",
    )
    test_pipeline_quota = PipelineQuota(
        pipelineName="test_pipeline",
        defaultQuota=1000,
        minQuotaConsumed=500,
        quotaUnits="units",
        maxQuotaConsumed=5000,
    )
    test_pipeline = PipelineWithDetails(
        pipelineName=test_pipeline_name,
        pipelineVersion=1,
        description="test_description",
        displayName="test_display_name",
        type="test_type",
        inputs=[test_input_definition, test_input_definition_optional],
        outputs=[test_output_definition],
        pipelineQuota=test_pipeline_quota,
    )

    return test_pipeline
