# commands/quotas_commands.py

import logging

import click

from terralab.log import indented
from terralab.logic import quotas_logic
from terralab.utils import handle_api_exceptions

LOGGER = logging.getLogger(__name__)


@click.command(short_help="Get quota information")
@click.argument("pipeline_name")
@handle_api_exceptions
def quota(pipeline_name: str):
    """Get quota information for a specific PIPELINE_NAME pipeline"""
    quota_info = quotas_logic.get_user_quota(pipeline_name)
    quota_limit = quota_info.quota_limit
    quota_consumed = quota_info.quota_consumed
    quota_pipeline = quota_info.pipeline_name
    LOGGER.info(f"Pipeline: {quota_pipeline}")
    LOGGER.info(indented(f"Quota Limit: {quota_limit}"))
    LOGGER.info(indented(f"Quota Used: {quota_consumed}"))
    LOGGER.info(indented(f"Quota Available: {quota_limit - quota_consumed}"))
