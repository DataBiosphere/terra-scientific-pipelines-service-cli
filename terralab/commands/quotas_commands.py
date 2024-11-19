# commands/quotas_commands.py

import logging

import click

from terralab.log import indented
from terralab.logic import quotas_logic
from terralab.utils import handle_api_exceptions

LOGGER = logging.getLogger(__name__)


@click.group()
def quotas():
    """Commands to get information about user quotas"""


@quotas.command()
@click.argument("pipeline_name")
@handle_api_exceptions
def get_info(pipeline_name: str):
    """Get user quota information for a specific pipeline"""
    quota_info = quotas_logic.get_user_quota(pipeline_name)
    quota = quota_info.quota_limit
    quota_consumed = quota_info.quota_consumed
    quota_pipeline = quota_info.pipeline_name
    LOGGER.info(f"Pipeline: {quota_pipeline}")
    LOGGER.info(indented(f"Quota Limit: {quota}"))
    LOGGER.info(indented(f"Quota Used: {quota_consumed}"))
    LOGGER.info(indented(f"Quota Left: {quota - quota_consumed}"))
