# commands/pipeline_runs_commands.py

import click
import logging
import uuid

from teaspoons_client import AsyncPipelineRunResponse, GetPipelineRunsResponse

from terralab.logic import pipeline_runs_logic, pipelines_logic
from terralab.utils import handle_api_exceptions, process_json_to_dict, validate_job_id, format_timestamp
from terralab.log import indented, add_blankline_after

LOGGER = logging.getLogger(__name__)


@click.command(short_help="Submit a pipeline run")
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
    """Submit a pipeline run for a PIPELINE_NAME pipeline"""
    inputs_dict = process_json_to_dict(inputs)

    # validate inputs
    pipelines_logic.validate_pipeline_inputs(pipeline_name, inputs_dict)

    submitted_job_id = pipeline_runs_logic.prepare_upload_start_pipeline_run(
        pipeline_name, version, inputs_dict, description
    )

    LOGGER.info(f"Successfully started {pipeline_name} job {submitted_job_id}")


@click.command(short_help="Download all output files from a pipeline run")
@click.argument("pipeline_name", type=str)
@click.argument("job_id", type=str)
@click.option(
    "--local_destination",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    default=".",
    help="optional location to download results to. defaults to the current directory.",
)
@handle_api_exceptions
def download(pipeline_name: str, job_id: str, local_destination: str):
    """Download all output files from a PIPELINE_NAME pipeline run with JOB_ID identifier"""
    job_id_uuid: uuid.UUID = validate_job_id(job_id)

    pipeline_runs_logic.get_result_and_download_pipeline_run_outputs(
        pipeline_name, job_id_uuid, local_destination
    )

@click.command(short_help="Get the status of a pipeline run")
@click.argument("pipeline_name", type=str)
@click.argument("job_id", type=str)
@handle_api_exceptions
def status(pipeline_name: str, job_id: str):
    """Get the status of a PIPELINE_NAME pipeline run with JOB_ID identifier"""
    job_id_uuid: uuid.UUID = validate_job_id(job_id)

    response: AsyncPipelineRunResponse = pipeline_runs_logic.get_pipeline_run_status(
        pipeline_name, job_id_uuid
    )

    LOGGER.info(add_blankline_after(f"Job status for {job_id}: {response.job_report.status}"))

    if response.error_report:
        LOGGER.info(add_blankline_after(f"Error message: {response.error_report.message}"))

    # if response.pipeline_run_report.outputs:
    #     LOGGER.info(add_blankline_after("Download outputs using `terralab download`"))

    LOGGER.info("Pipeline run details:")
    LOGGER.info(indented(f"Description: {response.job_report.description}"))
    LOGGER.info(indented(f"Pipeline name: {response.pipeline_run_report.pipeline_name}"))
    LOGGER.info(indented(f"Pipeline version: {response.pipeline_run_report.pipeline_version}"))
    LOGGER.info(indented(f"Method version: {response.pipeline_run_report.wdl_method_version}"))
    LOGGER.info(indented(f"Time submitted: {format_timestamp(response.job_report.submitted)}"))
    if response.job_report.completed:
        LOGGER.info(indented(f"Time completed: {format_timestamp(response.job_report.completed)}"))

        
@click.command(short_help="List all pipeline runs")
@handle_api_exceptions
def list_jobs():
    response: GetPipelineRunsResponse = pipeline_runs_logic.get_pipeline_runs()
    if response.results:
        for pipeline_run in response.results:
            LOGGER.info(pipeline_run.job_id)
            LOGGER.info(indented(f"status: {pipeline_run.status}"))
            LOGGER.info(add_blankline_after(indented(f"description: {pipeline_run.description}")))
    if response.page_token:
        LOGGER.info(f"next page token: {response.page_token}")
                        
