# logic/account_logic.py

import logging

from terralab.config import CliConfig
from terralab.sam_helper import get_user_proxy_group

LOGGER = logging.getLogger(__name__)


def get_cloud_info(config: CliConfig, access_token: str) -> list[list[str]]:
    """Get cloud integration information for the logged-in user.

    :param config: Configuration object
    :param access_token: A valid access token for the logged-in user
    :return: A list of rows to display in the cloud-info table
    """
    proxy_group = get_user_proxy_group(config, access_token)
    return [
        ["Service Account", config.teaspoons_share_group],
        ["Your Proxy Group", proxy_group],
    ]
