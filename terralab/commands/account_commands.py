# commands/account_commands.py

import logging

import click

from terralab.log import format_table_no_header, indented, add_blankline_before
from terralab.logic import account_logic

LOGGER = logging.getLogger(__name__)


@click.command()
def account() -> None:
    """Get information about your account"""
    account_info = account_logic.get_account_info()
    LOGGER.info("Your Account")
    LOGGER.info(add_blankline_before(format_table_no_header(account_info)))

    rows = account_logic.get_cloud_info()
    LOGGER.info(add_blankline_before("Cloud Resource Sharing"))
    LOGGER.info(
        add_blankline_before(
            "To ensure that your cloud resources can be properly accessed by Broad Scientific Services, please share them with the following accounts:"
        )
    )
    LOGGER.info(add_blankline_before(format_table_no_header(rows)))
    emails = ", ".join(row[1] for row in rows)
    LOGGER.info(indented(f"\nCopy all: {emails}"))
