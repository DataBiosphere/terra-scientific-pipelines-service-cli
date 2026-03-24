# sam_helper.py

import logging
from urllib import request as urllibrequest, error as urlliberror

import jwt

from terralab.config import CliConfig
from terralab.constants import SUPPORT_EMAIL

LOGGER = logging.getLogger(__name__)

PROXY_GROUP_ENDPOINT = "/api/google/v1/user/proxyGroup/{email}"


def get_user_proxy_group(cli_config: CliConfig, access_token: str) -> str:
    """Get the proxy group email for the logged-in user from Sam.

    :param cli_config: Configuration object containing the Sam API URL
    :param access_token: A valid access token for the logged-in user
    :return: The proxy group email address
    """
    email = _get_email_from_token(access_token)
    url = f"{cli_config.sam_api_url}{PROXY_GROUP_ENDPOINT.format(email=email)}"
    LOGGER.debug(f"Fetching proxy group from Sam for user {email}")

    req = urllibrequest.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllibrequest.urlopen(req) as response:
            proxy_group: str = response.read().decode("utf-8").strip('"')
            return proxy_group
    except urlliberror.URLError as e:
        LOGGER.debug(f"Failed to retrieve proxy group from Sam: {e}")
        LOGGER.error(
            f"Failed to retrieve user info, please try again or contact support at {SUPPORT_EMAIL}"
        )
        raise


def _get_email_from_token(access_token: str) -> str:
    """Decode the JWT access token and return the user's email address."""
    # Note that we do not need to verify the JWT signature or expiration here, since we just need to
    # extract the email claim. Wherever the token is used downstream by a service, it'll be verified by that service.
    decoded = jwt.decode(
        access_token, options={"verify_signature": False, "verify_exp": False}
    )
    email: str = decoded["email"]
    return email
