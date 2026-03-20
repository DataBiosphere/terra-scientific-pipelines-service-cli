# commands/account_commands.py

import logging

import click

from terralab.config import load_config

LOGGER = logging.getLogger(__name__)


@click.command(name="cloud-info")
def cloud_info() -> None:
    """Get cloud integration information for your account"""
    config = load_config()
    LOGGER.info(f"Share Group: {config.teaspoons_share_group}")
