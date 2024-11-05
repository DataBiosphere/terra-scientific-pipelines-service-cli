# logic/submit_logic.py

import uuid
from teaspoons_client import PipelineRunsApi, PreparePipelineRunResponse, PreparePipelineRunRequestBody

from terralab.client import ClientWrapper


def prepare_pipeline_run(pipeline_name: str, job_id: uuid.UUID, pipeline_version: str, pipeline_inputs: dict) -> dict:
    prepare_pipeline_run_request_body: PreparePipelineRunRequestBody = PreparePipelineRunRequestBody(jobId=job_id, pipelineVersion=pipeline_version, pipelineInputs=pipeline_inputs)
    with ClientWrapper() as api_client:
        pipeline_runs_client = PipelineRunsApi(api_client=api_client)
        response: PreparePipelineRunResponse = pipeline_runs_client.prepare_pipeline_run(
            pipeline_name,
            prepare_pipeline_run_request_body)

        return response.file_input_upload_urls
