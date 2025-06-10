# commands/pipelines_commands.py

import logging

import click

from terralab.log import pad_column, format_table
from terralab.logic import pipelines_logic
from terralab.utils import handle_api_exceptions

LOGGER = logging.getLogger(__name__)


@click.group()
def pipelines() -> None:
    """Get information about available pipelines"""


@pipelines.command(name="list")
@handle_api_exceptions
def list_command() -> None:
    """List all available pipelines"""
    pipelines_list = pipelines_logic.list_pipelines()
    LOGGER.info(
        f"Found {len(pipelines_list)} available pipeline{'' if len(pipelines_list) == 1 else 's'}:"
    )

    pipelines_list_rows = [["Name", "Version", "Description"]]
    for pipeline in pipelines_list:
        pipelines_list_rows.append(
            [
                pipeline.pipeline_name,
                str(pipeline.pipeline_version),
                pipeline.description,
            ]
        )

    LOGGER.info(format_table(pipelines_list_rows))


@pipelines.command(short_help="Get information about a pipeline")
@click.argument("pipeline_name")
@click.option("--version", type=int, help="pipeline version, defaults to latest")
@handle_api_exceptions
def details(pipeline_name: str, version: int) -> None:
    """Get information about the PIPELINE_NAME pipeline"""
    pipeline_info = pipelines_logic.get_pipeline_info(pipeline_name, version)

    # format the information nicely
    col_width = 20

    LOGGER.info(
        f"{pad_column("Pipeline Name:", col_width)}{pipeline_info.pipeline_name}"
    )
    LOGGER.info(
        f"{pad_column("Pipeline Version:", col_width)}{pipeline_info.pipeline_version}"
    )
    LOGGER.info(f"{pad_column("Description:", col_width)}{pipeline_info.description}")
    LOGGER.info(
        f"{pad_column("Min Quota Consumed:", col_width)}{pipeline_info.pipeline_quota.min_quota_consumed} {pipeline_info.pipeline_quota.quota_units}"
    )
    LOGGER.info("Inputs:")

    inputs_for_usage = []
    for input_definition in pipeline_info.inputs:
        LOGGER.info(
            f"{pad_column("", col_width)}{input_definition.name} ({input_definition.type})"
        )
        inputs_for_usage.extend([f"--{input_definition.name}", "YOUR_VALUE_HERE"])
    inputs_string_for_usage = " ".join(inputs_for_usage)

    LOGGER.info(
        f"{pad_column("Example usage:", col_width)}terralab submit {pipeline_info.pipeline_name} {inputs_string_for_usage} --description 'YOUR JOB DESCRIPTION HERE'"
    )
