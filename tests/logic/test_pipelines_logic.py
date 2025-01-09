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


# constants used in tests
TEST_PIPELINE_NAME = "test_pipeline"


def test_list_pipelines(mock_pipelines_api):
    mock_pipeline = mock(
        {"pipeline_name": TEST_PIPELINE_NAME, "description": "Test Description"}
    )
    when(mock_pipelines_api).get_pipelines().thenReturn(
        mock({"results": [mock_pipeline]})
    )

    result = pipelines_logic.list_pipelines()

    assert len(result) == 1
    assert result[0].pipeline_name == TEST_PIPELINE_NAME
    assert result[0].description == "Test Description"


def test_get_pipeline_info(mock_pipelines_api):
    mock_pipeline = mock(
        {
            "pipeline_name": TEST_PIPELINE_NAME,
            "pipeline_version": 1,
            "description": "Test Description",
            "display_name": "Test Display Name",
            "type": "Test Type",
            "inputs": [],
        }
    )
    test_get_info_request = GetPipelineDetailsRequestBody(pipelineVersion=1)
    when(mock_pipelines_api).get_pipeline_details(
        TEST_PIPELINE_NAME, test_get_info_request
    ).thenReturn(mock_pipeline)

    result = pipelines_logic.get_pipeline_info(TEST_PIPELINE_NAME, 1)

    assert result == mock_pipeline


def test_get_pipeline_info_bad_pipeline_name(mock_pipelines_api):
    test_get_info_request = GetPipelineDetailsRequestBody(pipelineVersion=None)
    when(mock_pipelines_api).get_pipeline_details(
        TEST_PIPELINE_NAME, test_get_info_request
    ).thenRaise(ApiException(404, reason="Pipeline not found"))

    with pytest.raises(ApiException):
        pipelines_logic.get_pipeline_info(TEST_PIPELINE_NAME, None)

    verify(mock_pipelines_api).get_pipeline_details(
        TEST_PIPELINE_NAME, test_get_info_request
    )


def test_validate_pipeline_inputs_success():
    test_inputs_dict = {"input1": "value1", "input2": "value2"}

    mock_pipeline_info = mock()
    mock_input1 = mock()
    mock_input1.name = "input1"
    mock_input1.type = "STRING"
    mock_input2 = mock()
    mock_input2.name = "input2"
    mock_input2.type = "STRING"
    mock_pipeline_info.inputs = [mock_input1, mock_input2]

    when(pipelines_logic).get_pipeline_info(TEST_PIPELINE_NAME, 1).thenReturn(
        mock_pipeline_info
    )

    # Should succeed with valid inputs
    pipelines_logic.validate_pipeline_inputs(TEST_PIPELINE_NAME, 1, test_inputs_dict)


def test_validate_pipeline_inputs_extra_input_warning(capture_logs):
    test_inputs_dict = {
        "extra_key": "extra_value",
    }

    mock_pipeline_info = mock()
    mock_pipeline_info.inputs = []

    when(pipelines_logic).get_pipeline_info(TEST_PIPELINE_NAME, None).thenReturn(
        mock_pipeline_info
    )

    with pytest.raises(SystemExit):
        pipelines_logic.validate_pipeline_inputs(
            TEST_PIPELINE_NAME, None, test_inputs_dict
        )

    assert "Error: Unexpected input 'extra_key'." in capture_logs.text


def test_validate_pipeline_inputs_missing_input(capture_logs):
    mock_pipeline_info = mock()
    mock_input1 = mock()
    mock_input1.name = "input1"
    mock_input1.type = "STRING"
    mock_input2 = mock()
    mock_input2.name = "input2"
    mock_input2.type = "STRING"
    mock_pipeline_info.inputs = [mock_input1, mock_input2]

    when(pipelines_logic).get_pipeline_info(TEST_PIPELINE_NAME, None).thenReturn(
        mock_pipeline_info
    )

    with pytest.raises(SystemExit):
        pipelines_logic.validate_pipeline_inputs(
            TEST_PIPELINE_NAME, None, {"input1": "value1"}
        )

    assert "Error: Missing input 'input2'" in capture_logs.text


def test_validate_pipeline_inputs_missing_input_value(capture_logs):
    mock_pipeline_info = mock()
    mock_input1 = mock()
    mock_input1.name = "input1"
    mock_input1.type = "STRING"
    mock_pipeline_info.inputs = [mock_input1]

    when(pipelines_logic).get_pipeline_info(TEST_PIPELINE_NAME, None).thenReturn(
        mock_pipeline_info
    )

    with pytest.raises(SystemExit):
        pipelines_logic.validate_pipeline_inputs(
            TEST_PIPELINE_NAME, None, {"input1": None}
        )

    assert "Error: Missing value for input 'input1'" in capture_logs.text


def test_validate_pipeline_inputs_missing_file(capture_logs):
    mock_pipeline_info = mock()
    mock_file_input = mock()
    mock_file_input.name = "file_input"
    mock_file_input.type = "FILE"
    mock_pipeline_info.inputs = [mock_file_input]

    when(pipelines_logic).get_pipeline_info(TEST_PIPELINE_NAME, 0).thenReturn(
        mock_pipeline_info
    )

    with pytest.raises(SystemExit):
        pipelines_logic.validate_pipeline_inputs(
            TEST_PIPELINE_NAME, 0, {"file_input": "nonexistent_file.txt"}
        )

    assert (
        "Error: Could not find provided file for input 'file_input': 'nonexistent_file.txt'"
        in capture_logs.text
    )
