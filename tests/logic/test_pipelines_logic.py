# tests/logic/test_pipelines_logic.py

import os
import tempfile

import pytest
from mockito import when, mock, verify
from teaspoons_client import ApiException, GetPipelineDetailsRequestBody

from terralab.constants import (
    STRING_TYPE_KEY,
    FILE_TYPE_KEY,
    INTEGER_TYPE_KEY,
    STRING_ARRAY_TYPE_KEY,
)
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


STRING_INPUT_KEY = "string_input"
FILE_INPUT_KEY = "file_input"
STRING_ARRAY_INPUT_KEY = "array_input"
OPTIONAL_INPUT_KEY = "optional_input"

MISSING_INPUT_MSG = "Error: Missing input '{key}'."

TEST_VERSION = 1

validate_pipeline_inputs_testdata = [
    # input dict, include_file boolean, list(error messages) if failure (None = validates)
    ({STRING_INPUT_KEY: "foo", STRING_ARRAY_INPUT_KEY: ["foo", "bar"]}, None),
    (
        {
            STRING_INPUT_KEY: "foo",
            STRING_ARRAY_INPUT_KEY: ["foo", "bar"],
            OPTIONAL_INPUT_KEY: "2",
        },
        None,
    ),
    # failures:
    (
        {
            STRING_INPUT_KEY: "foo",
            STRING_ARRAY_INPUT_KEY: ["foo", "bar"],
            "extra_input": None,
        },
        ["Error: Unexpected input 'extra_input'."],
    ),
    (
        {
            STRING_INPUT_KEY: "foo",
            STRING_ARRAY_INPUT_KEY: ["foo", "bar"],
            "extra_input": "with a value",
        },
        ["Error: Unexpected input 'extra_input'."],
    ),
    (
        {},
        [
            MISSING_INPUT_MSG.format(key=STRING_INPUT_KEY),
            MISSING_INPUT_MSG.format(key=STRING_ARRAY_INPUT_KEY),
        ],
    ),
    ({STRING_INPUT_KEY: "foo"}, [MISSING_INPUT_MSG.format(key=STRING_ARRAY_INPUT_KEY)]),
    (
        {STRING_INPUT_KEY: "foo", STRING_ARRAY_INPUT_KEY: None},
        [f"Error: Missing value for input '{STRING_ARRAY_INPUT_KEY}'."],
    ),
    (
        {
            STRING_INPUT_KEY: "foo",
            STRING_ARRAY_INPUT_KEY: ["foo", "bar"],
            OPTIONAL_INPUT_KEY: None,
        },
        [f"Error: Missing value for input '{OPTIONAL_INPUT_KEY}'."],
    ),
]


@pytest.mark.parametrize("input,error_messages", validate_pipeline_inputs_testdata)
def test_validate_pipeline_inputs(input: dict, error_messages: list[str], capture_logs):
    # define mock input definitions
    mock_pipeline_info = mock()
    mock_input1 = mock()
    mock_input1.name = STRING_INPUT_KEY
    mock_input1.type = STRING_TYPE_KEY
    mock_input1.is_required = True
    mock_input2 = mock()
    mock_input2.name = STRING_ARRAY_INPUT_KEY
    mock_input2.type = STRING_ARRAY_TYPE_KEY
    mock_input2.is_required = True
    mock_input3 = mock()
    mock_input3.name = OPTIONAL_INPUT_KEY
    mock_input3.type = INTEGER_TYPE_KEY
    mock_input3.is_required = False

    mock_pipeline_info.inputs = [mock_input1, mock_input2, mock_input3]

    when(pipelines_logic).get_pipeline_info(
        TEST_PIPELINE_NAME, TEST_VERSION
    ).thenReturn(mock_pipeline_info)

    if error_messages:
        with pytest.raises(SystemExit):
            pipelines_logic.validate_pipeline_inputs(
                TEST_PIPELINE_NAME, TEST_VERSION, input
            )
        for message in error_messages:
            assert message in capture_logs.text
    else:
        # Should succeed with valid inputs
        pipelines_logic.validate_pipeline_inputs(
            TEST_PIPELINE_NAME, TEST_VERSION, input
        )


validate_pipeline_inputs_file_testdata = [
    # input dict, file_to_create (or None), list(error messages) if failure (None = validates)
    ({STRING_INPUT_KEY: "foo", FILE_INPUT_KEY: "test_file"}, "test_file", None),
    # failures:
    (
        {STRING_INPUT_KEY: "foo", FILE_INPUT_KEY: "test_file"},
        None,
        [
            f"Error: Could not find provided file for input '{FILE_INPUT_KEY}': 'test_file'."
        ],
    ),
    (
        {STRING_INPUT_KEY: "foo", FILE_INPUT_KEY: None},
        None,
        [f"Error: Missing value for input '{FILE_INPUT_KEY}'."],
    ),
]


@pytest.mark.parametrize(
    "input,file_to_create,error_messages", validate_pipeline_inputs_file_testdata
)
def test_validate_pipeline_inputs_file(
    input: dict, file_to_create: str, error_messages: list[str], capture_logs
):
    # define mock input definitions
    mock_pipeline_info = mock()
    mock_input1 = mock()
    mock_input1.name = STRING_INPUT_KEY
    mock_input1.type = STRING_TYPE_KEY
    mock_input1.is_required = True
    mock_input2 = mock()
    mock_input2.name = FILE_INPUT_KEY
    mock_input2.type = FILE_TYPE_KEY
    mock_input2.is_required = True

    mock_pipeline_info.inputs = [mock_input1, mock_input2]

    when(pipelines_logic).get_pipeline_info(
        TEST_PIPELINE_NAME, TEST_VERSION
    ).thenReturn(mock_pipeline_info)

    with tempfile.TemporaryDirectory() as tmpdirname:
        if file_to_create:
            # write the file locally
            test_local_file_path = os.path.join(tmpdirname, file_to_create)
            with open(file=test_local_file_path, mode="w") as f:
                f.write("Hello, World!")

            # update inputs with this file path (including the temp directory path)
            input[FILE_INPUT_KEY] = test_local_file_path

        if error_messages:
            with pytest.raises(SystemExit):
                pipelines_logic.validate_pipeline_inputs(
                    TEST_PIPELINE_NAME, TEST_VERSION, input
                )
            for message in error_messages:
                assert message in capture_logs.text
        else:
            # Should succeed with valid inputs
            pipelines_logic.validate_pipeline_inputs(
                TEST_PIPELINE_NAME, TEST_VERSION, input
            )
