# tests/test_sam_helper.py

import pytest
from mockito import mock, when, verify
from urllib.error import URLError

from terralab import sam_helper
from tests.conftest import capture_logs

pytestmark = pytest.mark.usefixtures("unstub_fixture")

TEST_ACCESS_TOKEN = "test_access_token"
TEST_EMAIL = "user@example.com"
TEST_PROXY_GROUP = "PROXY_1234567890@example.com"
TEST_SAM_API_URL = "https://not-real-sam"


@pytest.fixture
def mock_cli_config():
    config = mock({"sam_api_url": TEST_SAM_API_URL})
    return config


def test_get_user_proxy_group_success(mock_cli_config):
    when(sam_helper)._get_email_from_token(TEST_ACCESS_TOKEN).thenReturn(TEST_EMAIL)

    mock_response = mock()
    when(mock_response).read().thenReturn(f'"{TEST_PROXY_GROUP}"'.encode("utf-8"))
    when(mock_response).__enter__().thenReturn(mock_response)
    when(mock_response).__exit__(None, None, None).thenReturn(None)
    when(sam_helper.urllibrequest).urlopen(...).thenReturn(mock_response)

    result = sam_helper.get_user_proxy_group(mock_cli_config, TEST_ACCESS_TOKEN)

    assert result == TEST_PROXY_GROUP
    verify(sam_helper)._get_email_from_token(TEST_ACCESS_TOKEN)


def test_get_user_proxy_group_builds_correct_url(mock_cli_config):
    when(sam_helper)._get_email_from_token(TEST_ACCESS_TOKEN).thenReturn(TEST_EMAIL)

    mock_response = mock()
    when(mock_response).read().thenReturn(f'"{TEST_PROXY_GROUP}"'.encode("utf-8"))
    when(mock_response).__enter__().thenReturn(mock_response)
    when(mock_response).__exit__(None, None, None).thenReturn(None)

    captured_requests = []

    def capture_request(req):
        captured_requests.append(req)
        return mock_response

    when(sam_helper.urllibrequest).urlopen(...).thenAnswer(capture_request)

    sam_helper.get_user_proxy_group(mock_cli_config, TEST_ACCESS_TOKEN)

    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert (
        req.full_url == f"{TEST_SAM_API_URL}/api/google/v1/user/proxyGroup/{TEST_EMAIL}"
    )
    assert req.get_header("Authorization") == f"Bearer {TEST_ACCESS_TOKEN}"


def test_get_user_proxy_group_url_error(mock_cli_config, capture_logs):
    when(sam_helper)._get_email_from_token(TEST_ACCESS_TOKEN).thenReturn(TEST_EMAIL)
    when(sam_helper.urllibrequest).urlopen(...).thenRaise(
        URLError("connection refused")
    )

    with pytest.raises(URLError):
        sam_helper.get_user_proxy_group(mock_cli_config, TEST_ACCESS_TOKEN)

    assert "Failed to retrieve proxy group from Sam" in capture_logs.text


def test_get_email_from_token():
    # build a real (unsigned) JWT with an email claim
    import base64
    import json

    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    payload = (
        base64.urlsafe_b64encode(json.dumps({"email": TEST_EMAIL}).encode())
        .rstrip(b"=")
        .decode()
    )
    token = f"{header}.{payload}."

    result = sam_helper._get_email_from_token(token)

    assert result == TEST_EMAIL
