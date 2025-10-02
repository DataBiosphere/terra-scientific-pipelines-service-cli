from terralab.version_utils import get_version_info_file_path, check_version
from unittest.mock import patch, MagicMock
from datetime import date
import requests


def test_get_version_info_file_path():
    path = get_version_info_file_path()
    assert path.endswith("version_info.json")


@patch("terralab.version_utils.get_last_version_check_date")
@patch("terralab.version_utils.version")
@patch("terralab.version_utils.requests.get")
@patch("terralab.version_utils.update_last_version_check_date")
def test_check_version_same_version(
    mock_update_date, mock_requests_get, mock_version, mock_get_date
):
    """Test when installed version equals latest version - no warning should be logged"""
    # Mock that we haven't checked today
    mock_get_date.return_value = None

    # Mock installed version
    mock_version.return_value = "1.0.0"

    # Mock PyPI response with same version
    mock_response = MagicMock()
    mock_response.json.return_value = {"info": {"version": "1.0.0"}}
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response

    with patch("terralab.version_utils.LOGGER") as mock_logger:
        check_version()

        # Should not log a warning since versions are equal
        mock_logger.warning.assert_not_called()
        # Should not update the last check date since no newer version was found
        mock_update_date.assert_not_called()


@patch("terralab.version_utils.get_last_version_check_date")
@patch("terralab.version_utils.version")
@patch("terralab.version_utils.requests.get")
@patch("terralab.version_utils.update_last_version_check_date")
def test_check_version_newer_available(
    mock_update_date, mock_requests_get, mock_version, mock_get_date
):
    """Test when a newer version is available - warning should be logged"""
    # Mock that we haven't checked today
    mock_get_date.return_value = None

    # Mock installed version
    mock_version.return_value = "1.0.0"

    # Mock PyPI response with newer version
    mock_response = MagicMock()
    mock_response.json.return_value = {"info": {"version": "1.1.0"}}
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response

    with patch("terralab.version_utils.LOGGER") as mock_logger:
        check_version()

        # Should log a warning about newer version
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "A new version of terralab-cli (1.1.0) is available" in warning_call
        assert "You are using 1.0.0" in warning_call

        # Should update the last check date since a newer version was found
        mock_update_date.assert_called_once()


@patch("terralab.version_utils.get_last_version_check_date")
def test_check_version_already_checked_today(mock_get_date):
    """Test that version check is skipped if already checked today"""
    # Mock that we already checked today
    mock_get_date.return_value = date.today()

    with patch("terralab.version_utils.LOGGER") as mock_logger:
        with patch("terralab.version_utils.version") as mock_version:
            check_version()

            # Should log debug message about skipping
            mock_logger.debug.assert_called_once()
            debug_call = mock_logger.debug.call_args[0][0]
            assert "Skipping version check" in debug_call

            # Should not call version() since we skip early
            mock_version.assert_not_called()


@patch("terralab.version_utils.get_last_version_check_date")
@patch("terralab.version_utils.version")
@patch("terralab.version_utils.requests.get")
def test_check_version_request_exception(
    mock_requests_get, mock_version, mock_get_date
):
    """Test that request exceptions are handled gracefully"""
    # Mock that we haven't checked today
    mock_get_date.return_value = None

    # Mock installed version
    mock_version.return_value = "1.0.0"

    # Mock request exception
    mock_requests_get.side_effect = requests.exceptions.RequestException(
        "Network error"
    )

    with patch("terralab.version_utils.LOGGER") as mock_logger:
        # Should not raise exception
        check_version()

        # Should log debug message about failure
        mock_logger.debug.assert_called_once()
        debug_call = mock_logger.debug.call_args[0][0]
        assert "Version check failed" in debug_call


@patch("terralab.version_utils.get_last_version_check_date")
@patch("terralab.version_utils.version")
def test_check_version_package_not_found(mock_version, mock_get_date):
    """Test that PackageNotFoundError is handled gracefully"""
    # Mock that we haven't checked today
    mock_get_date.return_value = None

    # Mock PackageNotFoundError
    from importlib.metadata import PackageNotFoundError

    mock_version.side_effect = PackageNotFoundError("Package not found")

    with patch("terralab.version_utils.LOGGER") as mock_logger:
        # Should not raise exception
        check_version()

        # Should log debug message about failure
        mock_logger.debug.assert_called_once()
        debug_call = mock_logger.debug.call_args[0][0]
        assert "Version check failed" in debug_call
