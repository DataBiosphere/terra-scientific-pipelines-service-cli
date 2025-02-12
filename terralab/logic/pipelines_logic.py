# logic/pipelines_logic.py

import logging
from typing import Any

from teaspoons_client import (  # type: ignore[attr-defined]
    GetPipelineDetailsRequestBody,
    Pipeline,
    PipelinesApi,
    PipelineUserProvidedInputDefinition,
    PipelineWithDetails,
)

from terralab.client import ClientWrapper
from terralab.constants import (
    FILE_TYPE_KEY,
)
from terralab.log import join_lines, add_blankline_before
from terralab.utils import is_valid_local_file

LOGGER = logging.getLogger(__name__)


def list_pipelines() -> list[Pipeline]:
    """List all pipelines, returning a list of Pipeline objects."""
    with ClientWrapper() as api_client:
        pipeline_client = PipelinesApi(api_client=api_client)
        pipelines = pipeline_client.get_pipelines()

        return [pipeline for pipeline in pipelines.results]


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


def validate_pipeline_inputs(
    pipeline_name: str, version: int, inputs_dict: dict[str, Any]
) -> None:
    """Validate pipeline inputs against required parameters and file existence.
    Exits with error if validation fails."""
    pipeline_info = get_pipeline_info(pipeline_name, version)
    errors = []

    # validate all expected inputs
    for input_def in pipeline_info.inputs:
        if error := _validate_single_input(input_def, inputs_dict):
            errors.append(error)

    # check for unexpected inputs
    expected_inputs = {input_def.name for input_def in pipeline_info.inputs}
    unexpected_inputs = set(inputs_dict.keys()) - expected_inputs
    if unexpected_inputs:
        errors.extend(
            f"Error: Unexpected input '{input_name}'."
            for input_name in unexpected_inputs
        )

    if errors:
        LOGGER.error(add_blankline_before(join_lines(errors)))
        exit(1)


def _validate_single_input(
    input_def: PipelineUserProvidedInputDefinition, inputs_dict: dict[str, Any]
) -> str | None:
    """Validate a single input definition against provided inputs.
    Returns error message if validation fails, None otherwise."""
    input_name = input_def.name

    if input_name not in inputs_dict:
        if input_def.is_required:
            return f"Error: Missing input '{input_name}'."
        return None

    input_value = inputs_dict[input_name]
    if input_value is None:
        return f"Error: Missing value for input '{input_name}'."

    if input_def.type == FILE_TYPE_KEY and not is_valid_local_file(input_value):
        return f"Error: Could not find provided file for input '{input_name}': '{input_value}'."

    return None
