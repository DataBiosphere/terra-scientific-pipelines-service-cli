# utils.py

import datetime
import json
import logging
import os
import requests
import tzlocal
import uuid
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from functools import wraps

from teaspoons_client import ApiException

from terralab.constants import SUPPORT_EMAIL_TEXT
from terralab.log import add_blankline_before


LOGGER = logging.getLogger(__name__)


def handle_api_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApiException as e:
            formatted_message = f"API call failed with status code {e.status} ({e.reason}): {json.loads(e.body)['message']}"
            LOGGER.error(add_blankline_before(formatted_message))
            LOGGER.error(add_blankline_before(SUPPORT_EMAIL_TEXT))
            exit(1)
        except Exception as e:
            LOGGER.error(add_blankline_before(str(e)))
            LOGGER.error(add_blankline_before(SUPPORT_EMAIL_TEXT))
            exit(1)

    return wrapper


def process_inputs_to_dict(inputs: tuple) -> dict:
    """Process command line arguments (input as a tuple) into a dictionary.

    Handles arguments in the format:
    - '--key value'
    - '--key=value'
    - '--flag' (value will be None)

    Args:
        inputs: Tuple of string arguments, generated by Click

    Returns:
        Dictionary of processed key-value pairs

    Raises:
        ValueError: If arguments are improperly formatted or contain duplicate keys
    """
    inputs_dict = {}
    i = 0

    while i < len(inputs):
        current_arg = inputs[i]

        if not current_arg.startswith("--"):
            raise ValueError(
                f"Error: Invalid input key '{current_arg}'. All input keys must start with '--'."
            )

        # strip leading dashes
        arg_without_dashes = current_arg[2:]

        if "=" in arg_without_dashes:
            # Handle --key=value format
            key, value = arg_without_dashes.split("=", 1)
            value = process_value(value)
        else:
            # Handle --key value or --flag format
            key = arg_without_dashes
            if i + 1 < len(inputs) and not inputs[i + 1].startswith("--"):
                value = process_value(inputs[i + 1])
                i += 1
            else:
                value = None

        if key in inputs_dict:
            raise ValueError(f"Error: Duplicate input key found: '{key}'.")

        LOGGER.debug(f"Processed input: {key}={value}")
        inputs_dict[key] = value
        i += 1

    return inputs_dict


def process_value(raw_value: str):
    """Process a raw input value string, splitting to an array if commas are present."""
    # process arrays
    if "," in raw_value:
        return raw_value.split(",")
    else:
        return raw_value


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
        LOGGER.info(add_blankline_before(f"File '{local_file_path}' upload complete"))
    except Exception as e:
        LOGGER.error(add_blankline_before(f"Error uploading file: {e}"))
        exit(1)


class SignedUrlDownload:
    """Class to generate and capture all the information needed to perform a download of a file based on a signed url."""

    def __init__(self, signed_url, local_destination_dir):
        self.signed_url = signed_url
        # extract file name from signed url; signed url looks like:
        # https://storage.googleapis.com/fc-secure-6970c3a9-dc92-436d-af3d-917bcb4cf05a/test_signed_urls/helloworld.txt?x-goog-signature...
        self.file_name = signed_url.split("?")[0].split("/")[-1]
        self.local_file_path = os.path.join(local_destination_dir, self.file_name)
        LOGGER.debug(f"Will download file to '{self.local_file_path}'")
        self.response = requests.get(signed_url, stream=True)

        self.response.raise_for_status()

        self.total_size_bytes = int(self.response.headers.get("content-length", 0))


def download_with_pbar(download: SignedUrlDownload) -> str:
    """Helper function to take a SignedUrlDownload object and perform a download with a progress bar.
    Return the local file path of the downloaded file."""
    download_block_size = 8192  # https://stackoverflow.com/questions/48719893/why-is-the-block-size-for-python-httplibs-reads-hard-coded-as-8192-bytes

    with open(download.local_file_path, "wb") as file:
        with tqdm(
            total=download.total_size_bytes,
            unit="B",
            unit_scale=True,
            desc=f"Downloading {download.file_name}",
            bar_format=PROGRESS_BAR_FORMAT,
            leave=False,  # remove progress bar when complete
            dynamic_ncols=True,  # play nice with window resizing
        ) as progress_bar:
            for data in download.response.iter_content(download_block_size):
                file.write(data)
                progress_bar.update(len(data))

    with logging_redirect_tqdm():  # log without interfering with progress bars
        LOGGER.info(f"Downloading {download.file_name}: complete")

    return download.local_file_path


def download_files_with_signed_urls(
    local_destination_dir: str, signed_urls: list[str]
) -> list[str]:
    """Downloads a file or multiple files in parallel, using signed urls, to a specified local destination.
    Returns a list of the local file path(s) of the downloaded file(s)."""

    try:
        downloads = [
            SignedUrlDownload(signed_url, local_destination_dir)
            for signed_url in signed_urls
        ]

        with ThreadPoolExecutor(max_workers=len(downloads)) as ex:
            downloaded_file_paths: list[str] = ex.map(download_with_pbar, downloads)
    except Exception as e:
        LOGGER.error(add_blankline_before(f"Error downloading files: {e}"))
        exit(1)

    LOGGER.info(add_blankline_before("All downloads complete"))
    return downloaded_file_paths


def validate_job_id(job_id: str) -> uuid.UUID:
    """Attempts to convert a string to a valid uuid.

    Returns the uuid if successful, otherwise logs an error and exits."""
    try:
        return uuid.UUID(job_id)
    except (TypeError, ValueError):
        LOGGER.error("Error: JOB_ID must be a valid uuid.")
        exit(1)


def format_timestamp(timestamp_string: str) -> str:
    """Formats a timestamp like 2024-11-20T21:05:57.907184Z to a nicely formatted string in the caller's timezone.
    If timestamp_str is None or empty, return an empty string."""
    if not (timestamp_string):
        return ""
    local_timezone = tzlocal.get_localzone()
    datetime_obj = datetime.datetime.fromisoformat(timestamp_string).astimezone(
        local_timezone
    )
    return datetime_obj.strftime("%Y-%m-%d %H:%M:%S %Z")
