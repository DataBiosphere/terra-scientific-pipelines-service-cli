# commands/service_commands.py

import click
import logging

from teaspoons_client import VersionProperties

from terralab.logic import service_logic
from terralab.utils import handle_api_exceptions
from terralab.log import indented

LOGGER = logging.getLogger(__name__)


@click.group()
def service():
    """Get information about the Teaspoons service"""


@service.command()
@handle_api_exceptions
def version():
    """Get the current deployed version of the Teaspoons service"""
    version_info: VersionProperties = service_logic.get_version()
    LOGGER.info("Teaspoons service version information:")
    LOGGER.info(indented(f"Git tag: {version_info.git_tag}"))
    LOGGER.info(indented(f"Git hash: {version_info.git_hash}"))
    LOGGER.info(indented(f"Build: {version_info.build}"))


@service.command()
@handle_api_exceptions
def status():
    """Get the current health status of the Teaspoons service"""
    status_string = service_logic.get_status()
    LOGGER.info(status_string)
