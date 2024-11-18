# commands/pipeline_runs_commands.py

import click
import logging

from terralab.logic import pipeline_runs_logic
from terralab.utils import handle_api_exceptions, process_json_to_dict
from terralab.logic import pipelines_logic

LOGGER = logging.getLogger(__name__)


@click.command()
@click.argument("pipeline_name")
@click.option(
    "--version", type=int, default=0, help="pipeline version; default: 0"
)  # once TSPS-370 is done, remove default
@click.option("--inputs", type=str, required=True, help="JSON string input")
@click.option(
    "--description", type=str, default="", help="optional description for the job"
)
@handle_api_exceptions
def submit(pipeline_name: str, version: int, inputs: str, description: str):
    """Submit a pipeline run"""
    inputs_dict = process_json_to_dict(inputs)

    # validate inputs
    pipelines_logic.validate_pipeline_inputs(pipeline_name, inputs_dict)

    submitted_job_id = pipeline_runs_logic.prepare_upload_start_pipeline_run(
        pipeline_name, version, inputs_dict, description
    )

    LOGGER.info(f"Successfully started {pipeline_name} job {submitted_job_id}")
