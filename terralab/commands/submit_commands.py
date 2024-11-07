# commands/submit_commands.py

import click
import logging

from terralab.logic import submit_logic
from terralab.utils import process_json, validate_pipeline_inputs, handle_api_exceptions

LOGGER = logging.getLogger(__name__)


@click.command()
@click.argument("pipeline_name")
@click.option("--version", type=int, default=0)
@click.option("--inputs", type=str, required=True, help='JSON string input')
@click.option("--description", type=str, default="", help='optional description for the job')
def submit(pipeline_name: str, version: int, inputs: str, description: str):
    """Command to submit a Teaspooons pipeline run"""
    inputs_dict = process_json(inputs)

    # validate inputs
    validate_pipeline_inputs(pipeline_name, inputs_dict)

    submitted_job_id = submit_logic.prepare_upload_start_pipeline_run(
        pipeline_name, version, inputs_dict, description)
    
    LOGGER.info(f"Successfully started {pipeline_name} job {submitted_job_id}")
