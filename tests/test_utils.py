# tests/test_utils

import os
import pytest
import tempfile

from mockito import mock, when
from terralab import utils
from tests.utils_for_tests import capture_logs

process_json_testdata = [
    # input, expected_output (failure = None)
    ("{}", {}),
    ('{"foo": "bar"}', {"foo": "bar"}),
    ('{"foo": {"bar": 2}}', {"foo": {"bar": 2}}),
    ("", None),
    ("string", None),
    (0, None),
    ([], None),
    ("[]", None),  # this is valid JSON but doesn't parse to a dict
    ("{[]}", None),
]


@pytest.mark.parametrize("input,expected_output", process_json_testdata)
def test_process_json_to_dict(input, expected_output):
    assert utils.process_json_to_dict(input) == expected_output


def test_is_valid_local_file():
    # existing file returns True
    with tempfile.TemporaryDirectory() as tmpdirname:
        test_local_file_name = "temp_file"
        test_local_file_path = os.path.join(tmpdirname, test_local_file_name)

        # write the file locally
        with open(file=test_local_file_path, mode="w") as blob_file:
            blob_file.write("Hello, World!")

        assert utils.is_valid_local_file(test_local_file_path)

    # nonexistent file returns False
    assert not (utils.is_valid_local_file("not a file"))


def test_validate_pipeline_inputs(capture_logs):
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

    when(utils).get_pipeline_info(test_pipeline_name).thenReturn(mock_pipeline_info)

    # Should succeed with valid inputs
    utils.validate_pipeline_inputs(test_pipeline_name, test_inputs_dict)

    # Should fail with missing input
    with pytest.raises(SystemExit):
        utils.validate_pipeline_inputs(test_pipeline_name, {"input1": "value1"})

    assert "Missing or invalid inputs provided" in capture_logs.text

    # Should fail with invalid file input
    mock_file_input = mock()
    mock_file_input.name = "file_input"
    mock_file_input.type = "FILE"
    mock_pipeline_info.inputs = [mock_file_input]

    when(utils).get_pipeline_info(test_pipeline_name).thenReturn(mock_pipeline_info)

    with pytest.raises(SystemExit):
        utils.validate_pipeline_inputs(
            test_pipeline_name, {"file_input": "nonexistent_file.txt"}
        )

    assert "Missing or invalid inputs provided" in capture_logs.text
