# logic/pipeline_runs_logic.py

import logging
import uuid
from typing import Any

from teaspoons_client import (  # type: ignore[attr-defined]
    AsyncPipelineRunResponse,
    JobControl,
    PipelineRun,
    PipelineRunsApi,
    PreparePipelineRunRequestBody,
    PreparePipelineRunResponse,
    StartPipelineRunRequestBody,
)

from terralab.client import ClientWrapper
from terralab.log import indented, add_blankline_before
from terralab.utils import upload_file_with_signed_url, download_files_with_signed_urls

LOGGER = logging.getLogger(__name__)


## API wrapper functions
SIGNED_URL_KEY = "signedUrl"


def prepare_pipeline_run(
    pipeline_name: str,
    job_id: str,
    pipeline_version: int,
    pipeline_inputs: dict[str, Any],
    description: str,
) -> dict[str, str]:
    """Call the preparePipelineRun Teaspoons endpoint.
    Return a dictionary of {input_name: signed_url}."""
    prepare_pipeline_run_request_body: PreparePipelineRunRequestBody = (
        PreparePipelineRunRequestBody(
            jobId=job_id,
            pipelineName=pipeline_name,
            pipelineVersion=pipeline_version,
            pipelineInputs=pipeline_inputs,
            description=description,
        )
    )

    with ClientWrapper() as api_client:
        pipeline_runs_client = PipelineRunsApi(api_client=api_client)
        response: PreparePipelineRunResponse = (
            pipeline_runs_client.prepare_pipeline_run(prepare_pipeline_run_request_body)
        )

        result = response.file_input_upload_urls

        return {
            input_name: signed_url_dict[SIGNED_URL_KEY]
            for input_name, signed_url_dict in result.items()
        }


def start_pipeline_run(job_id: str) -> str:
    """Call the startPipelineRun Teaspoons endpoint and return the Async Job Response."""
    start_pipeline_run_request_body: StartPipelineRunRequestBody = (
        StartPipelineRunRequestBody(jobControl=JobControl(id=job_id))
    )
    with ClientWrapper() as api_client:
        pipeline_runs_client = PipelineRunsApi(api_client=api_client)
        return pipeline_runs_client.start_pipeline_run(
            start_pipeline_run_request_body
        ).job_report.id


def get_pipeline_run_status(job_id: uuid.UUID) -> AsyncPipelineRunResponse:
    """Call the getPipelineRunResult Teaspoons endpoint and return the Async Pipeline Run Response."""

    with ClientWrapper() as api_client:
        pipeline_runs_client = PipelineRunsApi(api_client=api_client)
        return pipeline_runs_client.get_pipeline_run_result(str(job_id))


def get_pipeline_runs(n_results_requested: int) -> list[PipelineRun]:
    """Get the latest n_results_requested pipeline runs a user has submitted (most recent first)"""

    with ClientWrapper() as api_client:

        pipeline_runs_client = PipelineRunsApi(api_client=api_client)

        api_chunk_default = 10

        # fetch the first set of results
        response = pipeline_runs_client.get_all_pipeline_runs(
            limit=min(api_chunk_default, n_results_requested), page_token=None
        )
        results = list(response.results) if response.results else []
        LOGGER.debug(f"Retrieved {len(results)} PipelineRun results")
        page_token = response.page_token

        while len(results) < n_results_requested and page_token:
            response = pipeline_runs_client.get_all_pipeline_runs(
                limit=min(api_chunk_default, n_results_requested - len(results)),
                page_token=page_token,
            )
            new_results = list(response.results) if response.results else []
            results.extend(new_results)
            LOGGER.debug(
                f"Retrieved {len(new_results)} PipelineRun more results, totaling {len(results)}"
            )
            page_token = response.page_token
            if not (page_token):
                LOGGER.debug("Reached end of available PipelineRun results")

        return results


## submit action


def prepare_upload_start_pipeline_run(
    pipeline_name: str,
    pipeline_version: int,
    pipeline_inputs: dict[str, Any],
    description: str,
) -> str:
    """Prepare pipeline run, upload input files, and start pipeline run.
    Returns the uuid of the job."""
    # generate a job id for the user
    job_id = str(uuid.uuid4())
    LOGGER.info(f"Generated job_id {job_id}")

    file_input_upload_urls: dict[str, str] = prepare_pipeline_run(
        pipeline_name, job_id, pipeline_version, pipeline_inputs, description
    )

    for input_name, signed_url in file_input_upload_urls.items():
        input_file_value = pipeline_inputs[input_name]
        LOGGER.info(
            f"Uploading file `{input_file_value}` for {pipeline_name} input `{input_name}`"
        )
        LOGGER.debug(f"Found signed url: {signed_url}")

        upload_file_with_signed_url(input_file_value, signed_url)

    LOGGER.debug(f"Starting {pipeline_name} job {job_id}")

    return start_pipeline_run(job_id)


## download action


def get_result_and_download_pipeline_run_outputs(
    job_id: uuid.UUID, local_destination: str
) -> None:
    """Retrieve pipeline run result, download all output files."""
    LOGGER.info(
        f"Getting results for job {job_id} and downloading to {local_destination}"
    )
    result: AsyncPipelineRunResponse = get_pipeline_run_status(job_id)
    job_status: str = result.job_report.status
    LOGGER.debug(f"Job {job_id} status is {job_status}")
    if job_status != "SUCCEEDED":
        LOGGER.error(
            add_blankline_before(
                f"Results not available for job {job_id} with status {job_status}"
            )
        )
        exit(1)

    if not result.pipeline_run_report.outputs:
        LOGGER.error(
            add_blankline_before(
                f"Results for job {job_id} have expired. No results available."
            )
        )
        exit(1)

    # extract output signed urls and download them all
    signed_url_list: list[str] = list(result.pipeline_run_report.outputs.values())
    downloaded_files: list[str] = download_files_with_signed_urls(
        local_destination, signed_url_list
    )

    LOGGER.info("All file outputs downloaded:")
    for local_file_path in downloaded_files:
        LOGGER.info(indented(local_file_path))
