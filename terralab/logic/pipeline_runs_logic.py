# logic/pipeline_runs_logic.py

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

from terralab.utils import upload_file_with_signed_url, download_files_with_signed_urls
from terralab.client import ClientWrapper
from terralab.log import indented


LOGGER = logging.getLogger(__name__)


## API wrapper functions
SIGNED_URL_KEY = "signedUrl"


def prepare_pipeline_run(
    pipeline_name: str, job_id: str, pipeline_version: int, pipeline_inputs: dict
) -> dict:
    """Call the preparePipelineRun Teaspoons endpoint.
    Return a dictionary of {input_name: signed_url}."""
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

        result = response.file_input_upload_urls
        return {
            input_name: signed_url_dict.get(SIGNED_URL_KEY)
            for input_name, signed_url_dict in result.items()
        }


def start_pipeline_run(pipeline_name: str, job_id: str, description: str) -> uuid.UUID:
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
        ).job_report.id


def get_pipeline_run_status(
    pipeline_name: str, job_id: uuid.UUID
) -> AsyncPipelineRunResponse:
    """Call the getPipelineRunResult Teaspoons endpoint and return the Async Pipeline Run Response."""

    with ClientWrapper() as api_client:
        pipeline_runs_client = PipelineRunsApi(api_client=api_client)
        return pipeline_runs_client.get_pipeline_run_result(pipeline_name, str(job_id))


## submit action


def prepare_upload_start_pipeline_run(
    pipeline_name: str, pipeline_version: int, pipeline_inputs: dict, description: str
) -> uuid.UUID:
    """Prepare pipeline run, upload input files, and start pipeline run.
    Returns the uuid of the job."""
    # generate a job id for the user
    job_id = str(uuid.uuid4())
    LOGGER.info(f"Generated job_id {job_id}")

    file_input_upload_urls: dict = prepare_pipeline_run(
        pipeline_name, job_id, pipeline_version, pipeline_inputs
    )

    for input_name, signed_url in file_input_upload_urls.items():
        input_file_value = pipeline_inputs[input_name]
        LOGGER.info(
            f"Uploading file `{input_file_value}` for {pipeline_name} input `{input_name}`"
        )
        LOGGER.debug(f"Found signed url: {signed_url}")

        upload_file_with_signed_url(input_file_value, signed_url)

    LOGGER.debug(f"Starting {pipeline_name} job {job_id}")

    return start_pipeline_run(pipeline_name, job_id, description)


## download action


def get_result_and_download_pipeline_run_outputs(
    pipeline_name: str, job_id: uuid.UUID, local_destination: str
):
    """Retrieve pipeline run result, download all output files."""
    LOGGER.info(
        f"Getting results for {pipeline_name} run {job_id} and downloading to {local_destination}"
    )
    result: AsyncPipelineRunResponse = get_pipeline_run_status(pipeline_name, job_id)
    job_status: str = result.job_report.status
    LOGGER.debug(f"Job {job_id} status is {job_status}")
    if job_status != "SUCCEEDED":
        LOGGER.error(f"Results not available for job {job_id} with status {job_status}")
        exit(1)

    # extract output signed urls and download them all
    signed_url_list: list[str] = list(result.pipeline_run_report.outputs.values())
    downloaded_files: list[str] = download_files_with_signed_urls(
        local_destination, signed_url_list
    )

    LOGGER.info("All file outputs downloaded:")
    for local_file_path in downloaded_files:
        LOGGER.info(indented(local_file_path))
