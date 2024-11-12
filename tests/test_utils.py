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
