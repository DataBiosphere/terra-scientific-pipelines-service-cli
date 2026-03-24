# logic/account_logic.py

import logging

from terralab.auth_helper import get_or_refresh_access_token
from terralab.config import load_config
from terralab.sam_helper import get_user_proxy_group

LOGGER = logging.getLogger(__name__)


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
