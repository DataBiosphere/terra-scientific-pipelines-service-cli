# commands/pipeline_runs_commands.py

import click
import logging
import uuid

from teaspoons_client import AsyncPipelineRunResponse, PipelineRun

from terralab.logic import pipeline_runs_logic, pipelines_logic
from terralab.utils import (
    handle_api_exceptions,
    process_json_to_dict,
    validate_job_id,
    format_timestamp,
)
from terralab.log import (
    indented,
    add_blankline_after,
    format_table_with_status,
    format_status,
    pad_column,
)

LOGGER = logging.getLogger(__name__)


@click.command(short_help="Submit a job")
@click.argument("pipeline_name", type=str)
@click.option(
    "--version", type=int, default=0, help="pipeline version; default: 0"
)  # once TSPS-370 is done, remove default
@click.option("--inputs", type=str, required=True, help="JSON string input")
@click.option(
    "--description", type=str, default="", help="optional description for the job"
)
@handle_api_exceptions
def submit(pipeline_name: str, version: int, inputs: str, description: str):
    """Submit a job for a PIPELINE_NAME pipeline"""
    inputs_dict = process_json_to_dict(inputs)

    # validate inputs
    pipelines_logic.validate_pipeline_inputs(pipeline_name, inputs_dict)

    submitted_job_id = pipeline_runs_logic.prepare_upload_start_pipeline_run(
        pipeline_name, version, inputs_dict, description
    )

    LOGGER.info(f"Successfully started {pipeline_name} job {submitted_job_id}")


@click.command(short_help="Download all output files from a job")
@click.argument("pipeline_name", type=str)
@click.argument("job_id", type=str)
@click.option(
    "--local_destination",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    default=".",
    help="optional location to download results to. defaults to the current directory.",
)
@handle_api_exceptions
def download(pipeline_name: str, job_id: str, local_destination: str):
    """Download all output files from a PIPELINE_NAME job with JOB_ID identifier"""
    job_id_uuid: uuid.UUID = validate_job_id(job_id)

    pipeline_runs_logic.get_result_and_download_pipeline_run_outputs(
        pipeline_name, job_id_uuid, local_destination
    )


@click.command(short_help="Get the status and details of a job")
@click.argument("pipeline_name", type=str)
@click.argument("job_id", type=str)
@handle_api_exceptions
def details(pipeline_name: str, job_id: str):
    """Get the status and details of a PIPELINE_NAME pipeline job with JOB_ID identifier"""
    job_id_uuid: uuid.UUID = validate_job_id(job_id)

    response: AsyncPipelineRunResponse = pipeline_runs_logic.get_pipeline_run_status(
        pipeline_name, job_id_uuid
    )

    LOGGER.info(
        add_blankline_after(f"Status: {format_status(response.job_report.status)}")
    )

    if response.error_report:
        LOGGER.info(
            add_blankline_after(f"Error message: {response.error_report.message}")
        )

    LOGGER.info("Details:")
    col_size = 19
    LOGGER.info(
        indented(
            f'{pad_column("Pipeline name:", col_size)}{response.pipeline_run_report.pipeline_name}'
        )
    )
    LOGGER.info(
        indented(
            f'{pad_column("Pipeline version:", col_size)}{response.pipeline_run_report.pipeline_version}'
        )
    )
    LOGGER.info(
        indented(
            f'{pad_column("Submitted:", col_size)}{format_timestamp(response.job_report.submitted)}'
        )
    )
    if response.job_report.completed:
        LOGGER.debug(response.job_report.completed)
        LOGGER.info(
            indented(
                f'{pad_column("Completed:", col_size)}{format_timestamp(response.job_report.completed)}'
            )
        )
    LOGGER.info(
        indented(
            f'{pad_column("Description:", col_size)}{response.job_report.description}'
        )
    )


@click.command(short_help="List all jobs")
@click.option(
    "--num_results",
    type=int,
    default=10,
    help="Number of results to display. Defaults to 10.",
)
@handle_api_exceptions
def list_jobs(num_results: int):
    results: list[PipelineRun] = pipeline_runs_logic.get_pipeline_runs(num_results)
    if results:
        # create list of list of strings; first list is headers
        row_list = [["Job ID", "Status", "Submitted", "Completed", "Description"]]
        for pipeline_run in results:
            row_list.append(
                [
                    pipeline_run.job_id,
                    pipeline_run.status,
                    format_timestamp(pipeline_run.time_submitted),
                    format_timestamp(pipeline_run.time_completed),
                    pipeline_run.description,
                ]
            )

        LOGGER.info(format_table_with_status(row_list))
