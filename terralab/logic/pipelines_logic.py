# logic/pipelines_logic.py

import logging

from teaspoons_client import PipelinesApi, PipelineWithDetails, Pipeline

from terralab.client import ClientWrapper
from terralab.utils import is_valid_local_file

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


def get_pipeline_info(pipeline_name: str) -> PipelineWithDetails:
    """Get the details of a pipeline, returning a dictionary."""
    with ClientWrapper() as api_client:
        pipeline_client = PipelinesApi(api_client=api_client)
        return pipeline_client.get_pipeline_details(pipeline_name=pipeline_name)


def validate_pipeline_inputs(pipeline_name: str, inputs_dict: dict):
    """Check that all required user inputs are present, and that all file inputs are valid."""
    # retrieve required pipeline inputs; note currently this endpoint only returns required inputs
    pipeline_info: PipelineWithDetails = get_pipeline_info(pipeline_name)

    # TODO highlight the field name in the output so it's clearer
    input_error_messages = []
    for (
        input_info
    ) in pipeline_info.inputs:  # input_info is PipelineUserProvidedInputDefinition
        input_name: str = input_info.name
        LOGGER.debug(f"Validating input {input_name}")
        if input_name not in inputs_dict:
            input_error_messages.append(f"Missing required input {input_name}")
        else:
            # input is present in inputs_dict; if it's a file, extract the path and validate
            if input_info.type == "FILE" and (
                not is_valid_local_file(inputs_dict[input_name])
            ):
                input_error_messages.append(
                    f"Could not find provided file for input {input_name}: {inputs_dict[input_name]}"
                )

    if input_error_messages:
        error_string = "\n\t".join(input_error_messages)
        LOGGER.error(f"Missing or invalid inputs provided:\n\t{error_string}")
        exit(1)
