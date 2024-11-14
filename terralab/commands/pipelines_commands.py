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
    output_string = f"""Found {len(pipelines_list)} available pipeline{'' if len(pipelines_list) == 1 else 's'}:
"""
    for pipeline in pipelines_list:
        output_string += f"""
{pipeline.pipeline_name}
    {pipeline.description}"""

    LOGGER.info(output_string)


@pipelines.command()
@click.argument("pipeline_name")
@handle_api_exceptions
def get_info(pipeline_name: str):
    """Get information about a specific pipeline"""
    pipeline_info = pipelines_logic.get_pipeline_info(pipeline_name)

    inputs_for_main_log_message = []
    inputs_for_usage = []
    for input_definition in pipeline_info.inputs:
        inputs_for_main_log_message.append(
            f"""
                    {input_definition.name} ({input_definition.type})"""
        )
        inputs_for_usage.append(f'"{input_definition.name}": "YOUR_VALUE_HERE"')
    inputs_json_for_usage = f"{{{', '.join(inputs_for_usage)}}}"
    inputs_for_main_log_message = "".join(inputs_for_main_log_message)

    output_string = f"""Pipeline name:      {pipeline_info.pipeline_name}
Description:        {pipeline_info.description}
Inputs:{inputs_for_main_log_message}
Example usage:      terralab submit {pipeline_info.pipeline_name} --inputs '{inputs_json_for_usage}' --description 'YOUR JOB DESCRIPTION HERE'"""

    LOGGER.info(output_string)
