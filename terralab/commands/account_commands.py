# commands/account_commands.py

import logging

import click

from terralab.log import format_table_no_header
from terralab.logic import account_logic

LOGGER = logging.getLogger(__name__)


@click.command(
    name="account",
    short_help="Get information about sharing cloud resources with Broad Scientific Services",
)
def cloud_info() -> None:
    """Get cloud sharing information for your account"""
    rows = account_logic.get_cloud_info()
    LOGGER.info(
        "To ensure that your cloud resources can be properly accessed by Broad Scientific Services, please share them with the following accounts:\n"
    )
    LOGGER.info(format_table_no_header(rows))
    emails = ", ".join(row[1] for row in rows)
    LOGGER.info(f"\nCopy all: {emails}")
