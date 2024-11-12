# utils.py

import json
import logging
import os
import typing

from functools import wraps
from pydantic import BaseModel

from teaspoons_client import PipelineWithDetails
from teaspoons_client.exceptions import ApiException

from terralab.logic.pipelines_logic import get_pipeline_info


LOGGER = logging.getLogger(__name__)


def _pretty_print(obj: BaseModel):
    """
    Prints a pydantic model in a pretty format to the console
    """
    try:
        LOGGER.info(json.dumps(obj.model_dump(), indent=4))
    except Exception:
        LOGGER.error(obj)


def handle_api_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApiException as e:
            formatted_message = f"API call failed with status code {e.status} ({e.reason}): {json.loads(e.body)['message']}"
            LOGGER.error(formatted_message)
            exit(1)
        except Exception as e:
            LOGGER.error(str(e))
            exit(1)

    return wrapper


def process_json_to_dict(json_data) -> typing.Optional[dict]:
    """Process the given JSON string and return a dictionary.
    Returns None if the input string is not able to be parsed to a dictionary."""
    try:
        data = json.loads(json_data)
        if not (isinstance(data, dict)):
            raise TypeError
        LOGGER.debug(f"Processed inputs: {data}")
        return data
    except (json.JSONDecodeError, TypeError):
        LOGGER.error("Input string not parsable to a dictionary.")
        return None


def is_valid_local_file(local_file_path: str) -> bool:
    """Validate that the provided local file path exists."""
    return True if os.path.exists(local_file_path) else False


def validate_pipeline_inputs(pipeline_name: str, inputs_dict: dict):
    """Check that all required user inputs are present, and that all file inputs are valid."""
    # retrieve required pipeline inputs; note currently this endpoint only returns required inputs
    pipeline_info: PipelineWithDetails = get_pipeline_info(pipeline_name)

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
