# tests/logic/test_pipelines_logic.py

import pytest
from mockito import when, mock, verify

from teaspoons_client import ApiException, GetPipelineDetailsRequestBody

from terralab.logic import pipelines_logic

from tests.utils_for_tests import capture_logs


@pytest.fixture
def mock_cli_config(unstub):
    config = mock({"token_file": "mock_token_file"})
    when(pipelines_logic).CliConfig(...).thenReturn(config)
    yield config
    unstub()


@pytest.fixture
def mock_client_wrapper(unstub):
    client = mock()
    # Make the mock support context manager protocol
    when(client).__enter__().thenReturn(client)
    when(client).__exit__(None, None, None).thenReturn(None)

    when(pipelines_logic).ClientWrapper(...).thenReturn(client)
    yield client
    unstub()


@pytest.fixture
def mock_pipelines_api(mock_client_wrapper, unstub):
    api = mock()
    when(pipelines_logic).PipelinesApi(...).thenReturn(api)
    yield api
    unstub()


def test_list_pipelines(mock_pipelines_api):
    mock_pipeline = mock(
        {"pipeline_name": "Test Pipeline", "description": "Test Description"}
    )
    when(mock_pipelines_api).get_pipelines().thenReturn(
        mock({"results": [mock_pipeline]})
    )

    result = pipelines_logic.list_pipelines()

    assert len(result) == 1
    assert result[0].pipeline_name == "Test Pipeline"
    assert result[0].description == "Test Description"


def test_get_pipeline_info(mock_pipelines_api):
    pipeline_name = "Test Pipeline"
    mock_pipeline = mock(
        {
            "pipeline_name": pipeline_name,
            "pipeline_version": 1,
            "description": "Test Description",
            "display_name": "Test Display Name",
            "type": "Test Type",
            "inputs": [],
        }
    )
    test_get_info_request = GetPipelineDetailsRequestBody(pipelineVersion=1)
    when(mock_pipelines_api).get_pipeline_details(
        pipeline_name, test_get_info_request
    ).thenReturn(mock_pipeline)

    result = pipelines_logic.get_pipeline_info(pipeline_name, 1)

    assert result == mock_pipeline


def test_get_pipeline_info_bad_pipeline_name(mock_pipelines_api):
    pipeline_name = "Bad Pipeline Name"
    test_get_info_request = GetPipelineDetailsRequestBody(pipelineVersion=None)
    when(mock_pipelines_api).get_pipeline_details(
        pipeline_name, test_get_info_request
    ).thenRaise(ApiException(404, reason="Pipeline not found"))

    with pytest.raises(ApiException):
        pipelines_logic.get_pipeline_info(pipeline_name, None)

    verify(mock_pipelines_api).get_pipeline_details(
        pipeline_name, test_get_info_request
    )


def test_validate_pipeline_inputs_success():
    test_pipeline_name = "test_pipeline"
    test_inputs_dict = {"input1": "value1", "input2": "value2"}

    mock_pipeline_info = mock()
    mock_input1 = mock()
    mock_input1.name = "input1"
    mock_input1.type = "STRING"
    mock_input2 = mock()
    mock_input2.name = "input2"
    mock_input2.type = "STRING"
    mock_pipeline_info.inputs = [mock_input1, mock_input2]

    when(pipelines_logic).get_pipeline_info(test_pipeline_name, 1).thenReturn(
        mock_pipeline_info
    )

    # Should succeed with valid inputs
    pipelines_logic.validate_pipeline_inputs(test_pipeline_name, 1, test_inputs_dict)


def test_validate_pipeline_inputs_extra_input_warning(capture_logs):
    test_pipeline_name = "test_pipeline"

    test_inputs_dict = {
        "extra_key": "extra_value",
    }

    mock_pipeline_info = mock()
    mock_pipeline_info.inputs = []

    when(pipelines_logic).get_pipeline_info(test_pipeline_name, None).thenReturn(
        mock_pipeline_info
    )

    pipelines_logic.validate_pipeline_inputs(test_pipeline_name, None, test_inputs_dict)

    assert "Ignoring unexpected input `extra_key`" in capture_logs.text


def test_validate_pipeline_inputs_missing_input(capture_logs):
    test_pipeline_name = "test_pipeline"

    mock_pipeline_info = mock()
    mock_input1 = mock()
    mock_input1.name = "input1"
    mock_input1.type = "STRING"
    mock_input2 = mock()
    mock_input2.name = "input2"
    mock_input2.type = "STRING"
    mock_pipeline_info.inputs = [mock_input1, mock_input2]

    when(pipelines_logic).get_pipeline_info(test_pipeline_name, None).thenReturn(
        mock_pipeline_info
    )

    with pytest.raises(SystemExit):
        pipelines_logic.validate_pipeline_inputs(
            test_pipeline_name, None, {"input1": "value1"}
        )

    assert "Missing or invalid inputs provided" in capture_logs.text
    assert "Missing required input `input2`" in capture_logs.text


def test_validate_pipeline_inputs_missing_file(capture_logs):
    test_pipeline_name = "test_pipeline"
    mock_pipeline_info = mock()
    mock_file_input = mock()
    mock_file_input.name = "file_input"
    mock_file_input.type = "FILE"
    mock_pipeline_info.inputs = [mock_file_input]

    when(pipelines_logic).get_pipeline_info(test_pipeline_name, 0).thenReturn(
        mock_pipeline_info
    )

    with pytest.raises(SystemExit):
        pipelines_logic.validate_pipeline_inputs(
            test_pipeline_name, 0, {"file_input": "nonexistent_file.txt"}
        )

    assert "Missing or invalid inputs provided" in capture_logs.text
    assert (
        "Could not find provided file for input `file_input`: `nonexistent_file.txt`"
        in capture_logs.text
    )
