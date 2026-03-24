# sam_helper.py

import json
import logging
from urllib import request as urllibrequest, error as urlliberror

from terralab.config import CliConfig
from terralab.constants import SUPPORT_EMAIL

LOGGER = logging.getLogger(__name__)

SELF_INFO_ENDPOINT = "/api/users/v2/self"
PROXY_GROUP_ENDPOINT = "/api/google/v1/user/proxyGroup/{email}"


def get_user_email(cli_config: CliConfig, access_token: str) -> str:
    """Get the email address of the logged-in user from Sam.

    :param cli_config: Configuration object containing the Sam API URL
    :param access_token: A valid access token for the logged-in user
    :return: The user's email address
    """
    url = f"{cli_config.sam_api_url}{SELF_INFO_ENDPOINT}"
    LOGGER.debug("Fetching user info from Sam")

    req = urllibrequest.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllibrequest.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            email: str = data["email"]
            return email
    except urlliberror.URLError as e:
        LOGGER.debug(f"Failed to retrieve user info from Sam: {e}")
        LOGGER.error(
            f"Failed to retrieve user info, please try again or contact support at {SUPPORT_EMAIL}"
        )
        raise


def get_user_proxy_group(cli_config: CliConfig, access_token: str) -> str:
    """Get the proxy group email for the logged-in user from Sam.

    :param cli_config: Configuration object containing the Sam API URL
    :param access_token: A valid access token for the logged-in user
    :return: The proxy group email address
    """
    email = get_user_email(cli_config, access_token)
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
