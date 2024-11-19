# utils.py

import json
import logging
import os
import requests
import uuid
from tqdm import tqdm

from functools import wraps

from teaspoons_client import ApiException

from terralab.log import add_blankline_after


LOGGER = logging.getLogger(__name__)


def handle_api_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApiException as e:
            formatted_message = f"API call failed with status code {e.status} ({e.reason}): {json.loads(e.body)['message']}"
            LOGGER.error(add_blankline_after(formatted_message))
            exit(1)
        except Exception as e:
            LOGGER.error(add_blankline_after(str(e)))
            exit(1)

    return wrapper


def process_json_to_dict(json_data) -> dict:
    """Process the given JSON string and return a dictionary.
    Returns None if the input string is not able to be parsed to a dictionary."""
    try:
        data = json.loads(json_data)
        if not (isinstance(data, dict)):
            raise TypeError
        LOGGER.debug(f"Processed inputs: {data}")
        return data
    except (json.JSONDecodeError, TypeError):
        LOGGER.error(add_blankline_after("Input string not parsable to a dictionary."))
        exit(1)


def is_valid_local_file(local_file_path: str) -> bool:
    """Validate that the provided local file path exists."""
    return True if os.path.exists(local_file_path) else False


## upload and download methods
PROGRESS_BAR_FORMAT = "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [elapsed: {elapsed} ETA: {remaining} ({rate_fmt}{postfix})]"


def upload_file_with_signed_url(local_file_path, signed_url):
    """Uploads a local file using a signed URL"""
    try:
        with open(local_file_path, "rb") as in_file:
            total_bytes = os.fstat(in_file.fileno()).st_size
            with tqdm.wrapattr(
                in_file,
                "read",
                total=total_bytes,
                miniters=1,
                desc="Upload progress",
                bar_format=PROGRESS_BAR_FORMAT,
            ) as file_obj:
                response = requests.request(
                    method="PUT",
                    url=signed_url,
                    data=file_obj,
                    headers={"Content-Type": "application/octet-stream"},
                )
                response.raise_for_status()
        LOGGER.info(add_blankline_after(f"File `{local_file_path}` upload complete"))
    except Exception as e:
        LOGGER.error(add_blankline_after(f"Error uploading file: {e}"))
        exit(1)


def download_file_with_signed_url(local_destination_dir: str, signed_url: str) -> str:
    """Downloads a file to a local destination using a signed url.
    Returns the local file path of the downloaded file."""
    try:
        # extract file name from signed url; signed url looks like:
        # https://storage.googleapis.com/fc-secure-6970c3a9-dc92-436d-af3d-917bcb4cf05a/test_signed_urls/helloworld.txt?x-goog-signature...
        local_file_name = signed_url.split("?")[0].split("/")[-1]
        local_file_path = os.path.join(local_destination_dir, local_file_name)
        LOGGER.debug(f"Will download file to {local_file_path}")

        # download the file and write to local file
        response = requests.get(signed_url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024

        with open(local_file_path, "wb") as file:
            with tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc="Download progress",
                bar_format=PROGRESS_BAR_FORMAT,
            ) as progress_bar:
                for data in response.iter_content(block_size):
                    file.write(data)
                    progress_bar.update(len(data))

        LOGGER.info(add_blankline_after(f"File download complete: {local_file_path}"))
        return local_file_path

    except Exception as e:
        LOGGER.error(add_blankline_after(f"Error downloading file: {e}"))
        exit(1)


def validate_job_id(job_id: str) -> uuid.UUID:
    """Attempts to convert a string to a valid uuid.

    Returns the uuid if successful, otherwise logs an error and exits."""
    try:
        return uuid.UUID(job_id)
    except (TypeError, ValueError):
        LOGGER.error("Input error: JOB_ID must be a valid uuid.")
        exit(1)
