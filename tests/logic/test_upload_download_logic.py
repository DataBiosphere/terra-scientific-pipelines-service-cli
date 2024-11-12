# tests/test_upload_download_logic.py

import os
import tempfile
from mockito import when, mock

from terralab.logic import upload_download_logic
from tests.utils_for_tests import capture_logs


def test_upload_file_with_signed_url(capture_logs):
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

        when(upload_download_logic.requests).put(test_signed_url, ...).thenReturn(
            mock_response
        )

        # Act
        upload_download_logic.upload_file_with_signed_url(
            test_local_file_path, test_signed_url
        )

        # Assert
        assert "File uploaded successfully" in capture_logs.text
