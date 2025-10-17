# commands/pipelines_commands.py

import logging

import click

from terralab.log import (
    format_table_no_header,
    pad_column,
    format_table,
    add_blankline_before,
)
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

    # Pipeline information table
    pipeline_info_rows = [
        ["Pipeline Name", pipeline_info.pipeline_name, ""],
        ["Version", str(pipeline_info.pipeline_version), ""],
        ["Description", pipeline_info.description or "", ""],
        [
            "Min Quota Consumed",
            f"{pipeline_info.pipeline_quota.min_quota_consumed} {pipeline_info.pipeline_quota.quota_units.lower()}",
            "",
        ],
    ]
    LOGGER.info(format_table_no_header(pipeline_info_rows))

    inputs_for_usage = []
    optional_inputs = (
        []
    )  # we will display optional inputs at the end of the inputs list
    inputs_and_output_rows = [
        ["", "Name", "Type", "Description"],
        ["Inputs", "", "", ""],
    ]
    for input_def in pipeline_info.inputs:
        if not input_def.is_required:
            optional_inputs.append(
                [
                    "",
                    input_def.name,
                    input_def.type.lower(),
                    (
                        f"(optional) {input_def.description}"
                        if input_def.description
                        else "(optional)"
                    ),
                ]
            )
        else:
            inputs_for_usage.extend([f"--{input_def.name}", "YOUR_VALUE_HERE"])
            inputs_and_output_rows.append(
                [
                    "",
                    input_def.name,
                    input_def.type.lower(),
                    input_def.description or "",
                ]
            )
    if optional_inputs:
        inputs_and_output_rows.extend(optional_inputs)

    inputs_and_output_rows.extend([["Outputs", "", "", ""]])
    for output_def in pipeline_info.outputs:
        inputs_and_output_rows.append(
            ["", output_def.name, output_def.type.lower(), output_def.description or ""]
        )
    LOGGER.info(add_blankline_before(format_table_no_header(inputs_and_output_rows)))

    inputs_string_for_usage = " ".join(inputs_for_usage)
    LOGGER.info(
        add_blankline_before(
            f"{pad_column('Example usage', 20)}terralab submit {pipeline_info.pipeline_name} {inputs_string_for_usage} --description 'YOUR JOB DESCRIPTION HERE'"
        )
    )
