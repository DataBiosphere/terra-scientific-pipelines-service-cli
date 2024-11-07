# tests/test_utils

import pytest

from mockito import mock, when
from terralab import utils


process_json_testdata = [
    # input, expected_output (failure = None)
    ('{}', {}),
    ('{"foo": "bar"}', {"foo": "bar"}),
    ('{"foo": {"bar": 2}}', {"foo": {"bar": 2}}),
    ('', None),
    ('string', None),
    (0, None)
]

@pytest.mark.parametrize("input,expected_output", process_json_testdata)
def test_process_json(input, expected_output):
    assert utils.process_json(input) == expected_output
