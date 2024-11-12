# tests/test_upload_download_logic.py

import os
import pytest
import tempfile
from requests.exceptions import HTTPError
from mockito import when, mock

from terralab.logic import upload_download_logic
from tests.utils_for_tests import capture_logs


def test_upload_file_with_signed_url_success(capture_logs):
    # Arrange
    test_signed_url = "signed_url"

    with tempfile.TemporaryDirectory() as tmpdirname:
        test_local_file_name = "temp_file"
        test_local_file_path = os.path.join(tmpdirname, test_local_file_name)

        # write the file locally
        with open(file=test_local_file_path, mode="w") as blob_file:
            blob_file.write("Hello, World!")

        mock_response = mock()
        when(mock_response).raise_for_status()  # do nothing

        when(upload_download_logic.requests).request(...).thenReturn(mock_response)

        # Act
        upload_download_logic.upload_file_with_signed_url(
            test_local_file_path, test_signed_url
        )

        # Assert
        assert f"File {test_local_file_path} uploaded successfully" in capture_logs.text


def test_upload_file_with_signed_url_failed(capture_logs):
    # Arrange
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

        when(upload_download_logic.requests).request(...).thenReturn(mock_response)

        # Act
        with pytest.raises(SystemExit):
            upload_download_logic.upload_file_with_signed_url(
                test_local_file_path, test_signed_url
            )

        assert "Error uploading file: some message" in capture_logs.text
