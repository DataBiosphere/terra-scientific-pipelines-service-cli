# logic/account_logic.py

import logging

import jwt

from terralab.auth_helper import get_or_refresh_access_token
from terralab.config import load_config
from terralab.sam_helper import get_user_proxy_group, _get_email_from_token

LOGGER = logging.getLogger(__name__)


def get_account_info() -> list[list[str]]:
    """Get basic account information for the logged-in user from the JWT.

    :return: A list of rows to display in the account info table
    """
    config = load_config()
    access_token = get_or_refresh_access_token(config)
    decoded = jwt.decode(
        access_token, options={"verify_signature": False, "verify_exp": False}
    )
    name = decoded.get("name", "")
    email = _get_email_from_token(access_token)
    return [
        ["Name", name],
        ["Email Address", email],
    ]


def get_cloud_info() -> list[list[str]]:
    """Get cloud integration information for the logged-in user.

    :return: A list of rows to display in the cloud-info table
    """
    config = load_config()
    access_token = get_or_refresh_access_token(config)
    proxy_group = get_user_proxy_group(config, access_token)
    return [
        ["Service Account", config.teaspoons_share_group],
        ["Your Proxy Group", proxy_group],
    ]
