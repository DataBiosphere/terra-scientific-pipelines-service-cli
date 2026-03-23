# commands/account_commands.py

import logging

import click

from terralab.auth_helper import get_or_refresh_access_token
from terralab.config import load_config
from terralab.log import format_table_no_header
from terralab.sam_helper import get_user_proxy_group

LOGGER = logging.getLogger(__name__)


@click.command(name="cloud-info")
def cloud_info() -> None:
    """Get cloud sharing information for your account"""
    config = load_config()
    access_token = get_or_refresh_access_token(config)
    proxy_group = get_user_proxy_group(config, access_token)
    rows = [
        ["Service Account", config.teaspoons_share_group],
        ["Your Proxy Group", proxy_group],
    ]
    LOGGER.info(
        "To ensure that your cloud resources can be properly accessed by Broad Scientific Services, please share them with the following accounts:"
    )
    LOGGER.info("")
    LOGGER.info(format_table_no_header(rows))
