# tests/logic/test_pipeline_runs_logic.py

import uuid

import pytest
from mockito import when, mock, verify, times
from teaspoons_client import (
    ApiException,
    PreparePipelineRunRequestBody,
    StartPipelineRunRequestBody,
    JobControl,
)

from terralab.logic import pipeline_runs_logic
from tests.conftest import capture_logs

pytestmark = pytest.mark.usefixtures("unstub_fixture")


@pytest.fixture
def mock_cli_config():
    config = mock({"token_file": "mock_token_file"})
    when(pipeline_runs_logic).load_config(...).thenReturn(config)
    yield config


@pytest.fixture
def mock_client_wrapper():
    client = mock()
    # Make the mock support context manager protocol
    when(client).__enter__().thenReturn(client)
    when(client).__exit__(...).thenReturn(
        None
    )  # accept any arguments for __exit__, i.e. support exit(1)

    when(pipeline_runs_logic).ClientWrapper(...).thenReturn(client)
    yield client


@pytest.fixture
def mock_pipeline_runs_api(mock_client_wrapper):
    api = mock()
    when(pipeline_runs_logic).PipelineRunsApi(...).thenReturn(api)
    yield api


def test_prepare_pipeline_run_local_input(mock_pipeline_runs_api):
    test_job_id = str(uuid.uuid4())
    test_pipeline_name = "foobar"
    test_pipeline_version = 1
    test_pipeline_inputs = {}
    test_description = "i am a description"
    test_prepare_pipeline_run_request_body = PreparePipelineRunRequestBody(
        jobId=test_job_id,
        pipelineName=test_pipeline_name,
        pipelineVersion=test_pipeline_version,
        pipelineInputs=test_pipeline_inputs,
        description=test_description,
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
    when(mock_pipeline_runs_api).prepare_pipeline_run_v2(
        test_prepare_pipeline_run_request_body
    ).thenReturn(mock_pipeline_run_response)

    result = pipeline_runs_logic.prepare_pipeline_run(
        test_pipeline_name,
        test_job_id,
        test_pipeline_version,
        test_pipeline_inputs,
        test_description,
    )

    assert result == {test_input_name: test_signed_url}
    verify(mock_pipeline_runs_api).prepare_pipeline_run_v2(
        test_prepare_pipeline_run_request_body
    )


def test_prepare_pipeline_run_local_input_no_description(mock_pipeline_runs_api):
    test_job_id = str(uuid.uuid4())
    test_pipeline_name = "foobar"
    test_pipeline_version = 1
    test_pipeline_inputs = {}
    test_description = ""  # if no description is provided to command, it gets passed here as an empty string
    test_prepare_pipeline_run_request_body = PreparePipelineRunRequestBody(
        jobId=test_job_id,
        pipelineName=test_pipeline_name,
        pipelineVersion=test_pipeline_version,
        pipelineInputs=test_pipeline_inputs,
        description=test_description,
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
    when(mock_pipeline_runs_api).prepare_pipeline_run_v2(
        test_prepare_pipeline_run_request_body
    ).thenReturn(mock_pipeline_run_response)

    result = pipeline_runs_logic.prepare_pipeline_run(
        test_pipeline_name,
        test_job_id,
        test_pipeline_version,
        test_pipeline_inputs,
        test_description,
    )

    assert result == {test_input_name: test_signed_url}
    verify(mock_pipeline_runs_api).prepare_pipeline_run_v2(
        test_prepare_pipeline_run_request_body
    )


def test_prepare_pipeline_run_cloud_input(mock_pipeline_runs_api):
    test_job_id = str(uuid.uuid4())
    test_pipeline_name = "foobar"
    test_pipeline_version = 1
    test_input_name = "test_input"
    test_input_value = "gs://bucket/file"
    test_pipeline_inputs = {test_input_name: test_input_value}
    test_description = "i am a description"
    test_prepare_pipeline_run_request_body = PreparePipelineRunRequestBody(
        jobId=test_job_id,
        pipelineName=test_pipeline_name,
        pipelineVersion=test_pipeline_version,
        pipelineInputs=test_pipeline_inputs,
        description=test_description,
    )

    mock_pipeline_run_response = mock({"job_id": test_job_id})
    mock_pipeline_run_response.file_input_upload_urls = None  # service should not return signed urls when inputs are cloud files; this seems odd to have to mock a None value rather than the key not existing, which is what happens in the service, but this is how the mockito library handles missing keys
    when(mock_pipeline_runs_api).prepare_pipeline_run_v2(
        test_prepare_pipeline_run_request_body
    ).thenReturn(mock_pipeline_run_response)

    result = pipeline_runs_logic.prepare_pipeline_run(
        test_pipeline_name,
        test_job_id,
        test_pipeline_version,
        test_pipeline_inputs,
        test_description,
    )

    assert result is None
    verify(mock_pipeline_runs_api).prepare_pipeline_run_v2(
        test_prepare_pipeline_run_request_body
    )


def test_start_pipeline_run_running(mock_pipeline_runs_api):
    test_job_id = str(uuid.uuid4())

    test_start_pipeline_run_request_body = StartPipelineRunRequestBody(
        jobControl=JobControl(id=test_job_id)
    )
    mock_job_report = mock(
        {"id": test_job_id, "status_code": 202}
    )  # successful (running) status code
    mock_async_pipeline_run_response = mock({"job_report": mock_job_report})
    when(mock_pipeline_runs_api).start_pipeline_run(
        test_start_pipeline_run_request_body
    ).thenReturn(mock_async_pipeline_run_response)

    result = pipeline_runs_logic.start_pipeline_run(test_job_id)

    assert result == test_job_id
    verify(mock_pipeline_runs_api).start_pipeline_run(
        test_start_pipeline_run_request_body
    )


def test_start_pipeline_run_error_response(mock_pipeline_runs_api):
    test_job_id = str(uuid.uuid4())

    test_start_pipeline_run_request_body = StartPipelineRunRequestBody(
        jobControl=JobControl(id=test_job_id)
    )
    mock_job_report = mock(
        {"id": test_job_id, "status_code": 500}
    )  # internal error status code
    mock_error_report = mock({"message": "some error message"})
    mock_async_pipeline_run_response = mock(
        {"job_report": mock_job_report, "error_report": mock_error_report}
    )
    when(mock_pipeline_runs_api).start_pipeline_run(
        test_start_pipeline_run_request_body
    ).thenReturn(mock_async_pipeline_run_response)

    response = pipeline_runs_logic.start_pipeline_run(test_job_id)

    assert response == test_job_id
    verify(mock_pipeline_runs_api).start_pipeline_run(
        test_start_pipeline_run_request_body
    )


def test_prepare_upload_start_pipeline_run_local_input():
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
        test_pipeline_name,
        test_job_id_str,
        test_pipeline_version,
        test_inputs,
        test_description,
    ).thenReturn(test_upload_url_dict)

    when(pipeline_runs_logic).upload_file_with_signed_url(
        test_input_value, test_signed_url
    )  # do nothing

    when(pipeline_runs_logic).start_pipeline_run(test_job_id_str).thenReturn(
        test_job_id
    )

    response = pipeline_runs_logic.prepare_upload_start_pipeline_run(
        test_pipeline_name, test_pipeline_version, test_inputs, test_description
    )

    assert response == test_job_id


def test_prepare_upload_start_pipeline_run_cloud_input():
    test_pipeline_name = "foobar"
    test_pipeline_version = 0
    test_input_name = "input_name"
    test_input_value = "gs://bucket/cloud_value"
    test_inputs = {test_input_name: test_input_value}
    test_description = "user-provided description"

    test_job_id = uuid.uuid4()
    test_job_id_str = str(test_job_id)
    when(pipeline_runs_logic.uuid).uuid4().thenReturn(test_job_id)

    when(pipeline_runs_logic).prepare_pipeline_run(
        test_pipeline_name,
        test_job_id_str,
        test_pipeline_version,
        test_inputs,
        test_description,
    ).thenReturn()

    when(pipeline_runs_logic).start_pipeline_run(test_job_id_str).thenReturn(
        test_job_id
    )

    response = pipeline_runs_logic.prepare_upload_start_pipeline_run(
        test_pipeline_name, test_pipeline_version, test_inputs, test_description
    )

    assert response == test_job_id
    verify(pipeline_runs_logic, times(0)).upload_file_with_signed_url(...)


def test_get_pipeline_run_status(mock_pipeline_runs_api):
    test_job_id = uuid.uuid4()
    test_job_id_str = str(test_job_id)

    mock_job_report = mock({"id": test_job_id})
    mock_async_pipeline_run_response = mock({"job_report": mock_job_report})

    when(mock_pipeline_runs_api).get_pipeline_run_result_v2(test_job_id_str).thenReturn(
        mock_async_pipeline_run_response
    )

    response = pipeline_runs_logic.get_pipeline_run_status(test_job_id)

    assert response == mock_async_pipeline_run_response
    verify(mock_pipeline_runs_api).get_pipeline_run_result_v2(test_job_id_str)


def test_get_pipeline_run_output_signed_urls(mock_pipeline_runs_api):
    test_job_id = uuid.uuid4()
    test_job_id_str = str(test_job_id)

    test_output_name = "output1"
    test_signed_url = "signed_url"
    pipeline_run_output_signed_urls = {test_output_name: test_signed_url}
    mock_pipeline_run_output_signed_urls_response = mock(
        {"output_signed_urls": pipeline_run_output_signed_urls, "status": 200}
    )

    when(mock_pipeline_runs_api).get_pipeline_run_output_signed_urls(
        test_job_id_str
    ).thenReturn(mock_pipeline_run_output_signed_urls_response)

    response = pipeline_runs_logic.get_pipeline_run_output_signed_urls(test_job_id)

    assert response == mock_pipeline_run_output_signed_urls_response
    verify(mock_pipeline_runs_api).get_pipeline_run_output_signed_urls(test_job_id_str)


def test_get_pipeline_runs(mock_pipeline_runs_api):
    test_n_results_requested = 15
    test_pipeline_runs_10 = [mock() for _ in range(10)]
    n_total_results = 20

    # mock first response
    mock_first_response = mock(
        {"results": test_pipeline_runs_10, "total_results": n_total_results}
    )

    # mock second response with remaining results
    mock_second_response = mock(
        {"results": test_pipeline_runs_10[:5], "total_results": n_total_results}
    )

    when(mock_pipeline_runs_api).get_all_pipeline_runs_v2(
        page_number=1, page_size=10
    ).thenReturn(mock_first_response)

    # second request should only ask for 5, since the user requested 15 and we've returned 10 so far
    when(mock_pipeline_runs_api).get_all_pipeline_runs_v2(
        page_number=2, page_size=5
    ).thenReturn(mock_second_response)

    results = pipeline_runs_logic.get_pipeline_runs(test_n_results_requested)

    assert len(results) == test_n_results_requested
    verify(mock_pipeline_runs_api).get_all_pipeline_runs_v2(page_number=1, page_size=10)
    verify(mock_pipeline_runs_api).get_all_pipeline_runs_v2(page_number=2, page_size=5)


def test_get_pipeline_runs_requested_more_than_total(mock_pipeline_runs_api):
    test_n_results_requested = 15
    test_pipeline_runs_10 = [mock() for _ in range(10)]
    n_total_results = 12

    # mock first response of 10 results
    mock_first_response = mock(
        {"results": test_pipeline_runs_10, "total_results": n_total_results}
    )
    # mock second response of only 2 remaining results
    mock_second_response = mock(
        {"results": test_pipeline_runs_10[:2], "total_results": n_total_results}
    )

    when(mock_pipeline_runs_api).get_all_pipeline_runs_v2(
        page_number=1, page_size=10
    ).thenReturn(mock_first_response)

    # second request should only ask for 5, since the user requested 15 and we've returned 10 so far
    when(mock_pipeline_runs_api).get_all_pipeline_runs_v2(
        page_number=2, page_size=5
    ).thenReturn(mock_second_response)

    results = pipeline_runs_logic.get_pipeline_runs(test_n_results_requested)

    assert len(results) == n_total_results
    verify(mock_pipeline_runs_api).get_all_pipeline_runs_v2(page_number=1, page_size=10)
    verify(mock_pipeline_runs_api).get_all_pipeline_runs_v2(page_number=2, page_size=5)


def test_get_pipeline_runs_single_page(mock_pipeline_runs_api):
    test_n_results_requested = 5
    test_pipeline_runs_5 = [mock() for _ in range(5)]
    n_total_results = 20

    # mock response
    mock_response = mock(
        {"results": test_pipeline_runs_5, "total_results": n_total_results}
    )

    when(mock_pipeline_runs_api).get_all_pipeline_runs_v2(
        page_number=1, page_size=5
    ).thenReturn(mock_response)

    results = pipeline_runs_logic.get_pipeline_runs(test_n_results_requested)

    assert len(results) == test_n_results_requested
    verify(mock_pipeline_runs_api).get_all_pipeline_runs_v2(page_number=1, page_size=5)


def test_get_pipeline_runs_empty(mock_pipeline_runs_api):
    test_n_results_requested = 10

    # mock empty response
    mock_response = mock({"results": [], "total_results": 0})

    when(mock_pipeline_runs_api).get_all_pipeline_runs_v2(
        page_number=1, page_size=10
    ).thenReturn(mock_response)

    results = pipeline_runs_logic.get_pipeline_runs(test_n_results_requested)

    assert len(results) == 0
    verify(mock_pipeline_runs_api).get_all_pipeline_runs_v2(page_number=1, page_size=10)


def test_get_signed_urls_and_download_pipeline_run_outputs(capture_logs):
    test_job_id = uuid.uuid4()
    test_local_destination = "local/path"

    # mock signed url response
    test_output_name = "output1"
    test_signed_url = "signed_url"
    pipeline_run_output_signed_urls = {test_output_name: test_signed_url}
    pipeline_run_output_signed_urls_response = mock(
        {"output_signed_urls": pipeline_run_output_signed_urls, "status": 200}
    )

    when(pipeline_runs_logic).get_pipeline_run_output_signed_urls(
        test_job_id
    ).thenReturn(pipeline_run_output_signed_urls_response)

    expected_downloaded_file_paths = ["i am a file path"]
    when(pipeline_runs_logic).download_files_with_signed_urls(
        test_local_destination, [test_signed_url]
    ).thenReturn(
        expected_downloaded_file_paths
    )  # do nothing

    pipeline_runs_logic.get_signed_urls_and_download_pipeline_run_outputs(
        test_job_id, test_local_destination
    )
    assert f"Getting output signed URLs for job {test_job_id}" in capture_logs.text
    assert "All file outputs downloaded" in capture_logs.text

    verify(pipeline_runs_logic).get_pipeline_run_output_signed_urls(test_job_id)
    verify(pipeline_runs_logic).download_files_with_signed_urls(
        test_local_destination, [test_signed_url]
    )


def test_get_result_and_download_pipeline_run_outputs_error():
    test_job_id = uuid.uuid4()
    test_local_destination = "local/path"

    when(pipeline_runs_logic).get_pipeline_run_output_signed_urls(
        test_job_id
    ).thenRaise(ApiException(400, reason="error message"))

    with pytest.raises(ApiException):
        pipeline_runs_logic.get_signed_urls_and_download_pipeline_run_outputs(
            test_job_id, test_local_destination
        )

    # note that the error gets handled by @handle_api_exceptions, outside of this function
    verify(pipeline_runs_logic).get_pipeline_run_output_signed_urls(test_job_id)


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
