# tests/test_utils

import os
import tempfile
import uuid
import zoneinfo
from unittest.mock import patch

import pytest
from mockito import mock, when
from requests.exceptions import HTTPError
from urllib3.exceptions import MaxRetryError
from terralab import utils
from terralab.utils import handle_api_exceptions
from tests.conftest import capture_logs

process_inputs_testdata = [
    # input tuple, expected_output (failure = None)
    # note that the inputs will only ever have strings in them, never integers etc
    ((), {}),
    (("--foo", "foo_value"), {"foo": "foo_value"}),
    (("--foo", "3"), {"foo": "3"}),
    (
        ("--foo", "foo_value", "--bar", "bar_value"),
        {"foo": "foo_value", "bar": "bar_value"},
    ),
    (
        ("--foo=foo_value", "--bar", "bar_value"),
        {"foo": "foo_value", "bar": "bar_value"},
    ),
    (
        ("--array_input", "v1,v2,v3", "--bar", "bar_value"),
        {"array_input": ["v1", "v2", "v3"], "bar": "bar_value"},
    ),
    (
        ("--array_input=v1,v2,v3", "--bar", "bar_value"),
        {"array_input": ["v1", "v2", "v3"], "bar": "bar_value"},
    ),
    (
        ("--foo", "--bar"),
        {"foo": None, "bar": None},
    ),  # missing input values are parsed as None
    # failures:
    (("foo"), None),  # missing input key
    (("3"), None),  # missing input key, note integers get processed to strings
    (("--foo", "foo_value", "bar"), None),  # missing input value
    (
        ("--foo", "foo_value_1", "--foo", "foo_value_2"),
        None,
    ),  # duplicate key with second value
    (("--foo", "foo_value_1", "--foo"), None),  # duplicate key without second value
    (("--foo=foo_value", "bar"), None),
]


@pytest.mark.parametrize("input,expected_output", process_inputs_testdata)
def test_process_inputs_to_dict(input, expected_output):
    if expected_output is None:
        # failure
        with pytest.raises(ValueError):
            utils.process_inputs_to_dict(input)
    else:
        assert utils.process_inputs_to_dict(input) == expected_output


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


def test_validate_file_size_within_limit():
    with tempfile.TemporaryDirectory() as tmpdirname:
        test_file_path = os.path.join(tmpdirname, "small_file.txt")

        # Create a file with 10 MB (well under 1 GB limit)
        file_size_mb = 10
        with open(test_file_path, mode="wb") as f:
            f.write(b"0" * (file_size_mb * 1024 * 1024))

        # Should return None (no error)
        result = utils.validate_file_size(test_file_path)
        assert result is None


@patch("terralab.constants.MAX_FILE_UPLOAD_SIZE_BYTES", 1 * 1024 * 1024)  # 1 MB
def test_validate_file_size_at_limit():
    with tempfile.TemporaryDirectory() as tmpdirname:
        test_file_path = os.path.join(tmpdirname, "at_limit_file.txt")

        # Create a file with exactly 1 MB
        test_max_size = 1 * 1024 * 1024  # 1 MB
        with open(test_file_path, "wb") as f:
            f.write(b"0" * test_max_size)

        # Should return None (no error) since it's exactly at the limit
        result = utils.validate_file_size(test_file_path)
        assert result is None


@patch("terralab.constants.MAX_FILE_UPLOAD_SIZE_BYTES", 1 * 1024 * 1024)  # 1 MB
def test_validate_file_size_exceeds_limit():
    with tempfile.TemporaryDirectory() as tmpdirname:
        test_file_path = os.path.join(tmpdirname, "large_file.txt")

        # Create a file with 1 MB + 1 byte (over the limit)
        test_max_size = 1 * 1024 * 1024  # 1 MB
        with open(test_file_path, "wb") as f:
            f.write(b"0" * (test_max_size + 1))

        # Should return an error message
        result = utils.validate_file_size(test_file_path)
        assert result is not None
        assert "Error: File" in result
        assert "exceeds the maximum file size" in result
        assert test_file_path in result


def test_upload_file_with_signed_url_success(capture_logs):
    test_signed_url = "signed_url"

    with tempfile.TemporaryDirectory() as tmpdirname:
        test_local_file_name = "temp_file"
        test_local_file_path = os.path.join(tmpdirname, test_local_file_name)

        # write the file locally
        with open(file=test_local_file_path, mode="w") as blob_file:
            blob_file.write("Hello, World!")

        mock_response = mock()
        when(mock_response).raise_for_status()  # do nothing

        when(utils.requests).request(...).thenReturn(mock_response)

        utils.upload_file_with_signed_url(test_local_file_path, test_signed_url)

        assert f"File '{test_local_file_path}' upload complete" in capture_logs.text


def test_upload_file_with_signed_url_failed(capture_logs):
    test_signed_url = "signed_url"

    with tempfile.TemporaryDirectory() as tmpdirname:
        test_local_file_name = "temp_file"
        test_local_file_path = os.path.join(tmpdirname, test_local_file_name)

        # write the file locally
        with open(file=test_local_file_path, mode="w") as blob_file:
            blob_file.write("Hello, World!")

        mock_response = mock()
        when(mock_response).raise_for_status().thenRaise(
            HTTPError("some message")
        )  # raise an error

        when(utils.requests).request(...).thenReturn(mock_response)

        with pytest.raises(SystemExit):
            utils.upload_file_with_signed_url(test_local_file_path, test_signed_url)

        assert "Error uploading file: some message" in capture_logs.text


def test_download_files_with_signed_urls_success(capture_logs):
    test_file_name = "filename.ext"
    test_signed_url = f"signed_url/{test_file_name}?headers"

    test_file_size = 2048

    mock_response = mock({"headers": {"content-length": test_file_size}})
    when(mock_response).raise_for_status()  # do nothing
    when(mock_response).iter_content(...).thenReturn([b"chunk1", b"chunk2"])

    with tempfile.TemporaryDirectory() as test_download_dest_dir:
        when(utils.requests).get(test_signed_url, stream=True).thenReturn(mock_response)

        local_file_paths = utils.download_files_with_signed_urls(
            test_download_dest_dir, [test_signed_url]
        )

        for local_file_path in local_file_paths:
            assert os.path.exists(local_file_path)

    assert "All downloads complete" in capture_logs.text
    assert f"Downloading {test_file_name}: complete" in capture_logs.text


def test_download_files_with_signed_urls_failed(capture_logs):
    test_file_name = "filename.ext"
    test_signed_url = f"signed_url/{test_file_name}?headers"

    test_file_size = 2048

    mock_response = mock({"headers": {"content-length": test_file_size}})
    when(mock_response).raise_for_status().thenRaise(
        HTTPError("some message")
    )  # raise an error

    with tempfile.TemporaryDirectory() as test_download_dest_dir:
        when(utils.requests).get(test_signed_url, stream=True).thenReturn(mock_response)

        with pytest.raises(SystemExit):
            utils.download_files_with_signed_urls(
                test_download_dest_dir, [test_signed_url]
            )

    assert "Error downloading files: some message" in capture_logs.text


def test_validate_uuid(capture_logs):
    # valid
    valid_uuid = uuid.uuid4()
    assert utils.validate_job_id(str(valid_uuid)) == valid_uuid

    # invalid (uuid conversion raises ValueError)
    with pytest.raises(SystemExit):
        utils.validate_job_id("not a uuid")
    assert "Error: JOB_ID must be a valid uuid." in capture_logs.text
    capture_logs.clear()

    # empty (uuid conversion raises TypeError)
    with pytest.raises(SystemExit):
        utils.validate_job_id(None)
    assert "Error: JOB_ID must be a valid uuid." in capture_logs.text


def test_server_unavailable_error(capture_logs):
    @handle_api_exceptions
    def mock_retry_function():
        raise MaxRetryError(None, "Just a test")

    with pytest.raises(SystemExit):
        mock_retry_function()

    assert (
        "Unable to connect to the server after multiple retries. "
        "The server may be down or unreachable. Please try again later."
        in capture_logs.text
    )


format_timestamp_testdata = [
    # input timestamp string, local timezone, expected formatted output
    (
        "2024-11-20T21:05:57.907184Z",
        "America/Detroit",
        "2024-11-20 16:05:57 EST",
    ),  # basic case: detroit
    (
        "2024-11-20T21:05:57.907184Z",
        "US/Eastern",
        "2024-11-20 16:05:57 EST",
    ),  # basic case: eastern
    (
        "2024-11-20T21:05:57.907184Z",
        "America/Los_Angeles",
        "2024-11-20 13:05:57 PST",
    ),  # different timezone
    (
        "2024-06-20T21:05:57.907184Z",
        "America/Detroit",
        "2024-06-20 17:05:57 EDT",
    ),  # daylight savings time
    ("", None, ""),  # empty string
    (None, None, ""),  # None value
    ("2023-01-01T00:00:00Z", "America/Detroit", "2022-12-31 19:00:00 EST"),  # midnight
    (
        "2023-06-15T13:30:45.123456+00:00",
        "UTC",
        "2023-06-15 13:30:45 UTC",
    ),  # with timezone offset
]


@pytest.mark.parametrize("timestamp,local_timezone,expected", format_timestamp_testdata)
def test_format_timestamp(timestamp, local_timezone, expected, unstub):
    if local_timezone:
        when(utils.tzlocal).get_localzone().thenReturn(
            zoneinfo.ZoneInfo(key=local_timezone)
        )

    formatted = utils.format_timestamp(timestamp)
    # Only check the date/time portion since timezone will vary by system
    assert formatted == expected

    unstub()
