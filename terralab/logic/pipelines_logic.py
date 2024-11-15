# logic/pipelines_logic.py

import logging

from teaspoons_client import PipelinesApi, PipelineWithDetails, Pipeline

from terralab.client import ClientWrapper
from terralab.utils import is_valid_local_file
from terralab.log import indented, join_lines, add_blankline_after

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

    input_error_messages = []
    expected_input_keys = []
    for input_info in pipeline_info.inputs:  # PipelineUserProvidedInputDefinition
        input_name: str = input_info.name
        expected_input_keys.append(input_name)
        LOGGER.debug(f"Validating input {input_name}")
        if input_name not in inputs_dict:
            input_error_messages.append(
                indented(f"Missing required input `{input_name}`")
            )
        else:
            # input is present in inputs_dict; if it's a file, extract the path and validate
            if input_info.type == "FILE" and (
                not is_valid_local_file(inputs_dict[input_name])
            ):
                input_error_messages.append(
                    indented(
                        f"Could not find provided file for input `{input_name}`: `{inputs_dict[input_name]}`"
                    )
                )

    input_warning_messages = []
    for provided_input_key in inputs_dict.keys():
        if provided_input_key not in expected_input_keys:
            input_warning_messages.append(
                f"Ignoring unexpected input `{provided_input_key}`"
            )

    if input_warning_messages:
        LOGGER.warning(add_blankline_after(join_lines(input_warning_messages)))

    if input_error_messages:
        LOGGER.error(
            add_blankline_after(
                join_lines(
                    ["Missing or invalid inputs provided:"] + input_error_messages
                )
            )
        )
        exit(1)
