# commands/pipeline_runs_commands.py

import logging
import uuid

import click
from teaspoons_client import AsyncPipelineRunResponse, PipelineRun  # type: ignore[attr-defined]

from terralab.constants import FAILED_KEY, SUPPORT_EMAIL_TEXT, SUCCEEDED_KEY
from terralab.log import (
    indented,
    add_blankline_before,
    format_table_with_status,
    format_status,
)
from terralab.logic import pipeline_runs_logic, pipelines_logic
from terralab.utils import (
    handle_api_exceptions,
    process_inputs_to_dict,
    validate_job_id,
    format_timestamp,
)

LOGGER = logging.getLogger(__name__)


@click.command(
    short_help="Submit a job",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.argument("pipeline_name", type=str)
@click.option("--version", type=int, help="pipeline version, defaults to latest")
@click.option(
    "--description", type=str, default="", help="optional description for the job"
)
@click.argument("inputs", nargs=-1, type=click.UNPROCESSED)
@handle_api_exceptions
def submit(
    pipeline_name: str, version: int, inputs: tuple[str, ...], description: str
) -> None:
    """Submit a job for a PIPELINE_NAME pipeline

    To see the required inputs for a given pipeline, use the `terralab pipelines details` command.
    """
    LOGGER.debug(f"inputs: {inputs}")
    inputs_dict = process_inputs_to_dict(inputs)
    LOGGER.debug(f"inputs processed to dict: {inputs_dict}")

    # validate inputs
    pipelines_logic.validate_pipeline_inputs(pipeline_name, version, inputs_dict)

    submitted_job_id = pipeline_runs_logic.prepare_upload_start_pipeline_run(
        pipeline_name, version, inputs_dict, description
    )

    LOGGER.info(f"Successfully started {pipeline_name} job {submitted_job_id}")


@click.command(short_help="Download all output files from a job")
@click.argument("job_id", type=str)
@click.option(
    "--local_destination",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    default=".",
    help="optional location to download results to. defaults to the current directory.",
)
@handle_api_exceptions
def download(job_id: str, local_destination: str) -> None:
    """Download all output files from a job with JOB_ID identifier"""
    job_id_uuid: uuid.UUID = validate_job_id(job_id)

    pipeline_runs_logic.get_result_and_download_pipeline_run_outputs(
        job_id_uuid, local_destination
    )


# JOBS group


@click.group()
def jobs() -> None:
    """Get information about your jobs"""


@jobs.command(short_help="Get the status and details of a job")
@click.argument("job_id", type=str)
@handle_api_exceptions
def details(job_id: str) -> None:
    """Get the status and details of a job with JOB_ID identifier"""
    job_id_uuid: uuid.UUID = validate_job_id(job_id)

    response: AsyncPipelineRunResponse = pipeline_runs_logic.get_pipeline_run_status(
        job_id_uuid
    )

    LOGGER.info(f"Status: {format_status(response.job_report.status)}")

    if response.error_report:
        LOGGER.info(
            add_blankline_before(f"Error message: {response.error_report.message}")
        )

    if response.job_report.status == FAILED_KEY:
        LOGGER.info(add_blankline_before(SUPPORT_EMAIL_TEXT))

    LOGGER.info(add_blankline_before("Details:"))
    LOGGER.info(
        indented(f"Pipeline Name: {response.pipeline_run_report.pipeline_name}")
    )
    LOGGER.info(
        indented(f"Pipeline Version: {response.pipeline_run_report.pipeline_version}")
    )
    LOGGER.info(
        indented(f"Submitted: {format_timestamp(response.job_report.submitted)}")
    )
    if response.job_report.completed:
        LOGGER.info(
            indented(f"Completed: {format_timestamp(response.job_report.completed)}")
        )
    if response.job_report.status == SUCCEEDED_KEY:
        LOGGER.info(
            indented(
                f"File Download Expiration: {format_timestamp(response.pipeline_run_report.output_expiration_date)}"
            )
        )
    LOGGER.info(indented(f"Description: {response.job_report.description}"))


@jobs.command(name="list", short_help="List your jobs")
@click.option(
    "--num_results",
    type=int,
    default=10,
    help="Number of results to display. Defaults to 10.",
)
@handle_api_exceptions
def list_command(num_results: int) -> None:
    results: list[PipelineRun] = pipeline_runs_logic.get_pipeline_runs(num_results)
    if results:
        # create list of list of strings; first list is headers
        row_list = [
            [
                "Job ID",
                "Pipeline Name",
                "Version",
                "Status",
                "Submitted",
                "Completed",
                "Description",
                "Quota Consumed",
            ]
        ]
        for pipeline_run in results:
            row_list.append(
                [
                    pipeline_run.job_id,
                    pipeline_run.pipeline_name,
                    str(pipeline_run.pipeline_version),
                    pipeline_run.status,
                    format_timestamp(pipeline_run.time_submitted),
                    format_timestamp(pipeline_run.time_completed),
                    pipeline_run.description or "",
                    (
                        str(pipeline_run.quota_consumed)
                        if pipeline_run.quota_consumed is not None
                        else ""
                    ),
                ]
            )

        LOGGER.info(format_table_with_status(row_list))
