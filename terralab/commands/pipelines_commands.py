# commands/pipelines_commands.py

import click
import logging

from terralab.logic import pipelines_logic
from terralab.utils import handle_api_exceptions
from terralab.log import indented, pad_column

LOGGER = logging.getLogger(__name__)


@click.group()
def pipelines():
    """Get information about available pipelines"""


@pipelines.command()
@handle_api_exceptions
def list():
    """List all available pipelines"""
    pipelines_list = pipelines_logic.list_pipelines()
    LOGGER.info(
        f"Found {len(pipelines_list)} available pipeline{'' if len(pipelines_list) == 1 else 's'}:"
    )

    for pipeline in pipelines_list:
        LOGGER.info(pipeline.pipeline_name)
        LOGGER.info(indented(pipeline.description))


@pipelines.command()
@click.argument("pipeline_name")
@handle_api_exceptions
def get_info(pipeline_name: str):
    """Get information about a specific pipeline"""
    pipeline_info = pipelines_logic.get_pipeline_info(pipeline_name)

    # format the information nicely
    col_width = 16

    LOGGER.info(
        f"{pad_column("Pipeline name:", col_width)}{pipeline_info.pipeline_name}"
    )
    LOGGER.info(f"{pad_column("Description:", col_width)}{pipeline_info.description}")
    LOGGER.info("Inputs:")

    inputs_for_usage = []
    for input_definition in pipeline_info.inputs:
        LOGGER.info(
            f"{pad_column("", col_width)}{input_definition.name} ({input_definition.type})"
        )
        inputs_for_usage.append(f'"{input_definition.name}": "YOUR_VALUE_HERE"')
    inputs_json_for_usage = f"{{{', '.join(inputs_for_usage)}}}"

    LOGGER.info(
        f"{pad_column("Example usage:", col_width)}terralab submit {pipeline_info.pipeline_name} --inputs '{inputs_json_for_usage}' --description 'YOUR JOB DESCRIPTION HERE'"
    )
