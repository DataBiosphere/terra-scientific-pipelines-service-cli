# tests/logic/test_pipeline_runs_logic.py

import pytest
import uuid
from mockito import when, mock, verify

from terralab.logic import pipeline_runs_logic
from teaspoons_client import (
    PreparePipelineRunRequestBody,
    StartPipelineRunRequestBody,
    JobControl,
)

from tests.utils_for_tests import capture_logs


@pytest.fixture
def mock_cli_config(unstub):
    config = mock({"token_file": "mock_token_file"})
    when(pipeline_runs_logic).CliConfig(...).thenReturn(config)
    yield config
    unstub()


@pytest.fixture
def mock_client_wrapper(unstub):
    client = mock()
    # Make the mock support context manager protocol
    when(client).__enter__().thenReturn(client)
    when(client).__exit__(None, None, None).thenReturn(None)

    when(pipeline_runs_logic).ClientWrapper(...).thenReturn(client)
    yield client
    unstub()


@pytest.fixture
def mock_pipeline_runs_api(mock_client_wrapper, unstub):
    api = mock()
    when(pipeline_runs_logic).PipelineRunsApi(...).thenReturn(api)
    yield api
    unstub()


def test_prepare_pipeline_run(mock_pipeline_runs_api):
    test_job_id = str(uuid.uuid4())
    test_pipeline_name = "foobar"
    test_pipeline_version = 1
    test_pipeline_inputs = {}
    test_prepare_pipeline_run_request_body = PreparePipelineRunRequestBody(
        jobId=test_job_id,
        pipelineVersion=test_pipeline_version,
        pipelineInputs=test_pipeline_inputs,
    )

    test_input_name = "test_input"
    test_signed_url = "signed_url"
    test_file_input_upload_urls_dict = {
        test_input_name: {pipeline_runs_logic.SIGNED_URL_KEY: test_signed_url}
    }
    mock_pipeline_run_response = mock(
        {
            "job_id": test_job_id,
            "file_input_upload_urls": test_file_input_upload_urls_dict,
        }
    )
    when(mock_pipeline_runs_api).prepare_pipeline_run(
        test_pipeline_name, test_prepare_pipeline_run_request_body
    ).thenReturn(mock_pipeline_run_response)

    result = pipeline_runs_logic.prepare_pipeline_run(
        test_pipeline_name, test_job_id, test_pipeline_version, test_pipeline_inputs
    )

    assert result == {test_input_name: test_signed_url}
    verify(mock_pipeline_runs_api).prepare_pipeline_run(
        test_pipeline_name, test_prepare_pipeline_run_request_body
    )


def test_start_pipeline_run_running(mock_pipeline_runs_api):
    test_job_id = str(uuid.uuid4())
    test_pipeline_name = "foobar"
    test_description = "user-provided description"

    test_start_pipeline_run_request_body = StartPipelineRunRequestBody(
        description=test_description, jobControl=JobControl(id=test_job_id)
    )
    mock_job_report = mock(
        {"id": test_job_id, "status_code": 202}
    )  # successful (running) status code
    mock_async_pipeline_run_response = mock({"job_report": mock_job_report})
    when(mock_pipeline_runs_api).start_pipeline_run(
        test_pipeline_name, test_start_pipeline_run_request_body
    ).thenReturn(mock_async_pipeline_run_response)

    result = pipeline_runs_logic.start_pipeline_run(
        test_pipeline_name, test_job_id, test_description
    )

    assert result == test_job_id
    verify(mock_pipeline_runs_api).start_pipeline_run(
        test_pipeline_name, test_start_pipeline_run_request_body
    )


def test_start_pipeline_run_error_response(mock_pipeline_runs_api):
    test_job_id = str(uuid.uuid4())
    test_pipeline_name = "foobar"
    test_description = "user-provided description"

    test_start_pipeline_run_request_body = StartPipelineRunRequestBody(
        description=test_description, jobControl=JobControl(id=test_job_id)
    )
    mock_job_report = mock(
        {"id": test_job_id, "status_code": 500}
    )  # internal error status code
    mock_error_report = mock({"message": "some error message"})
    mock_async_pipeline_run_response = mock(
        {"job_report": mock_job_report, "error_report": mock_error_report}
    )
    when(mock_pipeline_runs_api).start_pipeline_run(
        test_pipeline_name, test_start_pipeline_run_request_body
    ).thenReturn(mock_async_pipeline_run_response)

    response = pipeline_runs_logic.start_pipeline_run(
        test_pipeline_name, test_job_id, test_description
    )

    assert response == test_job_id
    verify(mock_pipeline_runs_api).start_pipeline_run(
        test_pipeline_name, test_start_pipeline_run_request_body
    )


def test_prepare_upload_start_pipeline_run():
    test_pipeline_name = "foobar"
    test_pipeline_version = 0
    test_input_name = "input_name"
    test_input_value = "value"
    test_inputs = {test_input_name: test_input_value}
    test_description = "user-provided description"

    test_job_id = uuid.uuid4()
    test_job_id_str = str(test_job_id)
    when(pipeline_runs_logic.uuid).uuid4().thenReturn(test_job_id)

    test_signed_url = "signed_url"
    test_upload_url_dict = {test_input_name: test_signed_url}
    when(pipeline_runs_logic).prepare_pipeline_run(
        test_pipeline_name, test_job_id_str, test_pipeline_version, test_inputs
    ).thenReturn(test_upload_url_dict)

    when(pipeline_runs_logic).upload_file_with_signed_url(
        test_input_value, test_signed_url
    )  # do nothing

    when(pipeline_runs_logic).start_pipeline_run(
        test_pipeline_name, test_job_id_str, test_description
    ).thenReturn(test_job_id)

    response = pipeline_runs_logic.prepare_upload_start_pipeline_run(
        test_pipeline_name, test_pipeline_version, test_inputs, test_description
    )

    assert response == test_job_id


def test_get_pipeline_run_status(mock_pipeline_runs_api):
    test_pipeline_name = "foobar"
    test_job_id = uuid.uuid4()
    test_job_id_str = str(test_job_id)

    mock_job_report = mock({"id": test_job_id})
    mock_async_pipeline_run_response = mock({"job_report": mock_job_report})

    when(mock_pipeline_runs_api).get_pipeline_run_result(
        test_pipeline_name, test_job_id_str
    ).thenReturn(mock_async_pipeline_run_response)

    response = pipeline_runs_logic.get_pipeline_run_status(
        test_pipeline_name, test_job_id
    )

    assert response == mock_async_pipeline_run_response
    verify(mock_pipeline_runs_api).get_pipeline_run_result(
        test_pipeline_name, test_job_id_str
    )


def test_get_result_and_download_pipeline_run_outputs(capture_logs):
    test_pipeline_name = "foobar"
    test_job_id = uuid.uuid4()
    test_local_destination = "local/path"

    # mock successful job status
    mock_job_report = mock({"status": "SUCCEEDED"})
    test_output_name = "output1"
    test_signed_url = "signed_url"
    mock_pipeline_run_report = mock({"outputs": {test_output_name: test_signed_url}})
    mock_async_pipeline_run_response = mock(
        {"job_report": mock_job_report, "pipeline_run_report": mock_pipeline_run_report}
    )

    when(pipeline_runs_logic).get_pipeline_run_status(
        test_pipeline_name, test_job_id
    ).thenReturn(mock_async_pipeline_run_response)

    expected_downloaded_file_paths = ["i am a file path"]
    when(pipeline_runs_logic).download_files_with_signed_urls(
        test_local_destination, [test_signed_url]
    ).thenReturn(
        expected_downloaded_file_paths
    )  # do nothing

    pipeline_runs_logic.get_result_and_download_pipeline_run_outputs(
        test_pipeline_name, test_job_id, test_local_destination
    )

    assert (
        f"Getting results for {test_pipeline_name} run {test_job_id}"
        in capture_logs.text
    )
    assert "All file outputs downloaded" in capture_logs.text

    verify(pipeline_runs_logic).get_pipeline_run_status(test_pipeline_name, test_job_id)
    verify(pipeline_runs_logic).download_files_with_signed_urls(
        test_local_destination, [test_signed_url]
    )


def test_get_result_and_download_pipeline_run_outputs_running(capture_logs):
    test_pipeline_name = "foobar"
    test_job_id = uuid.uuid4()
    test_local_destination = "local/path"

    # mock running job status
    mock_job_report = mock({"status": "RUNNING"})
    test_output_name = "output1"
    test_signed_url = "signed_url"
    mock_pipeline_run_report = mock({"outputs": {test_output_name: test_signed_url}})
    mock_async_pipeline_run_response = mock(
        {"job_report": mock_job_report, "pipeline_run_report": mock_pipeline_run_report}
    )

    when(pipeline_runs_logic).get_pipeline_run_status(
        test_pipeline_name, test_job_id
    ).thenReturn(mock_async_pipeline_run_response)

    with pytest.raises(SystemExit):
        pipeline_runs_logic.get_result_and_download_pipeline_run_outputs(
            test_pipeline_name, test_job_id, test_local_destination
        )

    assert (
        f"Results not available for job {test_job_id} with status RUNNING"
        in capture_logs.text
    )
    assert "Please wait until the pipeline run has completed" in capture_logs.text


def test_get_result_and_download_pipeline_run_outputs_failed(capture_logs):
    test_pipeline_name = "foobar"
    test_job_id = uuid.uuid4()
    test_local_destination = "local/path"

    # mock failed job status
    mock_job_report = mock({"status": "FAILED"})
    mock_pipeline_run_report = mock()
    mock_error_report = mock({"status_code": 500, "message": "something went wrong"})
    mock_async_pipeline_run_response = mock(
        {
            "job_report": mock_job_report,
            "pipeline_run_report": mock_pipeline_run_report,
            "error_report": mock_error_report,
        }
    )

    when(pipeline_runs_logic).get_pipeline_run_status(
        test_pipeline_name, test_job_id
    ).thenReturn(mock_async_pipeline_run_response)

    with pytest.raises(SystemExit):
        pipeline_runs_logic.get_result_and_download_pipeline_run_outputs(
            test_pipeline_name, test_job_id, test_local_destination
        )

    assert (
        f"Results not available for job {test_job_id} with status FAILED"
        in capture_logs.text
    )
    assert "Pipeline run failed: 500, something went wrong" in capture_logs.text


def create_mock_pipeline_run_result(
    status, error_status_code=None, error_status_message=None
):
    """Util for creating mock test pipeline run response objects"""
    # mock running job status
    mock_job_report = mock({"status": status})
    test_output_name = "output1"
    test_signed_url = "signed_url"
    mock_pipeline_run_report_with_outputs = mock(
        {"outputs": {test_output_name: test_signed_url}}
    )
    mock_error_report = mock(
        {"status_code": error_status_code, "message": error_status_message}
    )

    if status == "SUCCEEDED":
        return mock(
            {
                "job_report": mock_job_report,
                "pipeline_run_report": mock_pipeline_run_report_with_outputs,
            }
        )
    elif status == "FAILED":
        return mock(
            {
                "job_report": mock_job_report,
                "pipeline_run_report": mock(),
                "error_report": mock_error_report,
            }
        )
    else:  # PREPARING, RUNNING, or other status
        return mock({"job_report": mock_job_report, "pipeline_run_report": mock()})


handle_non_success_testdata = [
    # input, expected_output
    (create_mock_pipeline_run_result("SUCCEEDED"), None),
    (
        create_mock_pipeline_run_result("RUNNING"),
        "Please wait until the pipeline run has completed to download outputs.",
    ),
    (
        create_mock_pipeline_run_result("PREPARING"),
        "This job has not yet been started.",
    ),
    (
        create_mock_pipeline_run_result("FAILED", 500, "something went wrong"),
        "Pipeline run failed: 500, something went wrong",
    ),
    (create_mock_pipeline_run_result("WHAT"), "Unexpected pipeline run status WHAT"),
]


@pytest.mark.parametrize("input,expected_output", handle_non_success_testdata)
def test_handle_non_success(input, expected_output):
    assert pipeline_runs_logic.handle_non_success(input) == expected_output
