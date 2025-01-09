# logic/pipelines_logic.py

import logging

from teaspoons_client import (
    PipelinesApi,
    PipelineWithDetails,
    Pipeline,
    GetPipelineDetailsRequestBody,
)

from terralab.client import ClientWrapper
from terralab.utils import is_valid_local_file
from terralab.log import join_lines, add_blankline_before

LOGGER = logging.getLogger(__name__)


def list_pipelines() -> list[Pipeline]:
    """List all pipelines, returning a list of dictionaries."""
    with ClientWrapper() as api_client:
        pipeline_client = PipelinesApi(api_client=api_client)
        pipelines = pipeline_client.get_pipelines()

        result = []
        for pipeline in pipelines.results:
            result.append(pipeline)

        return result


def get_pipeline_info(pipeline_name: str, version: int) -> PipelineWithDetails:
    """Get the details of a pipeline, returning a dictionary."""
    get_pipeline_details_request_body: GetPipelineDetailsRequestBody = (
        GetPipelineDetailsRequestBody(pipelineVersion=version)
    )
    with ClientWrapper() as api_client:
        pipeline_client = PipelinesApi(api_client=api_client)
        return pipeline_client.get_pipeline_details(
            pipeline_name, get_pipeline_details_request_body
        )


def validate_pipeline_inputs(pipeline_name: str, version, inputs_dict: dict):
    """Check that all required user inputs are present, and that all file inputs are valid."""
    # retrieve required pipeline inputs; note currently this endpoint only returns required inputs
    pipeline_info: PipelineWithDetails = get_pipeline_info(pipeline_name, version)

    input_error_messages = []
    expected_input_keys = []
    for input_info in pipeline_info.inputs:  # PipelineUserProvidedInputDefinition
        input_name: str = input_info.name
        expected_input_keys.append(input_name)
        LOGGER.debug(f"Validating input {input_name}")
        if input_name not in inputs_dict:
            input_error_messages.append(
                f"Error: Missing input '{input_name}'."
            )
        else:  # input is present in inputs_dict
            # do not allow missing values
            if inputs_dict[input_name] is None:
                input_error_messages.append(
                    f"Error: Missing value for input '{input_name}'"
                )
                continue
            # if it's a file, extract the path and validate
            if input_info.type == "FILE" and (
                not is_valid_local_file(inputs_dict[input_name])
            ):
                input_error_messages.append(
                        f"Error: Could not find provided file for input '{input_name}': '{inputs_dict[input_name]}'."
                )

    # TODO don't allow None values
    for provided_input_key in inputs_dict.keys():
        if provided_input_key not in expected_input_keys:
            input_error_messages.append(
                f"Error: Unexpected input '{provided_input_key}'."
            )

    if input_error_messages:
        LOGGER.error(
            add_blankline_before(
                join_lines(
                    input_error_messages
                )
            )
        )
        exit(1)
