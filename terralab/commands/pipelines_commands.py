# commands/pipelines_commands.py

import click
import logging

from terralab.logic import pipelines_logic
from terralab.utils import handle_api_exceptions

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
        f"Found {len(pipelines_list)} available pipeline{'' if len(pipelines_list) == 1 else 's'}:\n"
    )
    for pipeline in pipelines_list:
        LOGGER.info(f"{pipeline.pipeline_name}\n\t{pipeline.description}\n")


@pipelines.command()
@click.argument("pipeline_name")
@handle_api_exceptions
def get_info(pipeline_name: str):
    """Get information about a specific pipeline"""
    n_spaces = 16
    pipeline_info = pipelines_logic.get_pipeline_info(pipeline_name)
    LOGGER.info(f"{'Pipeline name:'.ljust(n_spaces)}{pipeline_info.pipeline_name}")
    LOGGER.info(f"{'Description:'.ljust(n_spaces)}{pipeline_info.description}")
    LOGGER.info("Inputs: ")
    inputs_strings = []
    for input_definition in pipeline_info.inputs:
        LOGGER.info(
            f"{''.ljust(n_spaces)}{input_definition.name} ({input_definition.type})"
        )
        inputs_strings.append(f'"{input_definition.name}": "YOUR_VALUE_HERE"')
    inputs_str = f"{{{', '.join(inputs_strings)}}}"
    LOGGER.info(
        f"{'Example usage:'.ljust(n_spaces)}terralab submit {pipeline_info.pipeline_name} --inputs '{inputs_str}' --description 'YOUR JOB DESCRIPTION HERE'\n"
    )
