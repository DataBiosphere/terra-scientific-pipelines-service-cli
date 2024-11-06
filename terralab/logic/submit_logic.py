# logic/submit_logic.py

import logging
import uuid
from teaspoons_client import (
    PipelineRunsApi,
    PreparePipelineRunResponse,
    PreparePipelineRunRequestBody,
    StartPipelineRunRequestBody,
    JobControl,
    AsyncPipelineRunResponse,
)

from terralab.client import ClientWrapper


LOGGER = logging.getLogger(__name__)


## API wrapper functions

def prepare_pipeline_run(
    pipeline_name: str, job_id: uuid.UUID, pipeline_version: int, pipeline_inputs: dict
) -> dict:
    """Call the preparePipelineRun Teaspoons endpoint and return the dict of file input upload urls."""
    prepare_pipeline_run_request_body: PreparePipelineRunRequestBody = (
        PreparePipelineRunRequestBody(
            jobId=job_id,
            pipelineVersion=pipeline_version,
            pipelineInputs=pipeline_inputs,
        )
    )
    with ClientWrapper() as api_client:
        pipeline_runs_client = PipelineRunsApi(api_client=api_client)
        response: PreparePipelineRunResponse = (
            pipeline_runs_client.prepare_pipeline_run(
                pipeline_name, prepare_pipeline_run_request_body
            )
        )

        return response.file_input_upload_urls


def start_pipeline_run(
    pipeline_name: str, job_id: uuid.UUID, description: str
) -> uuid.UUID:
    """Call the startPipelineRun Teaspoons endpoint and return the Async Job Response."""
    start_pipeline_run_request_body: StartPipelineRunRequestBody = (
        StartPipelineRunRequestBody(
            description=description, jobControl=JobControl(id=job_id)
        )
    )
    with ClientWrapper() as api_client:
        pipeline_runs_client = PipelineRunsApi(api_client=api_client)
        return pipeline_runs_client.start_pipeline_run(
            pipeline_name, start_pipeline_run_request_body
        )


## submit action

def prepare_upload_start_pipeline_run(pipeline_name: str, pipeline_version: str, pipeline_inputs: dict, description: str) -> uuid.UUID:
    """Prepare pipeline run, upload input files, and start pipeline run.
    Returns the uuid of the job."""
    # generate a job id for the user
    job_id = str(uuid.uuid4())
    LOGGER.info(f"Generated job_id {job_id}")

    file_input_upload_urls: dict = prepare_pipeline_run(pipeline_name, job_id, pipeline_version, pipeline_inputs)

    for input_name, upload_url_dict in file_input_upload_urls.items():
        LOGGER.info(f"Uploading input {input_name}")
        LOGGER.info(f"Found signed url: {upload_url_dict['signedUrl']}")
        LOGGER.info("(SKIPPING UPLOAD FOR NOW)")
    
    # TODO implement upload, add start pipeline run

    return job_id
