# commands/pipeline_runs_commands.py

import click
import logging
import uuid

from terralab.logic import pipeline_runs_logic
from terralab.utils import handle_api_exceptions, process_json_to_dict, validate_job_id
from terralab.logic import pipelines_logic

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
