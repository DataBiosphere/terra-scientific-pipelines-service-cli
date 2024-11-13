# logic/upload_download_logic.py

import os
import logging
import requests
from tqdm import tqdm

LOGGER = logging.getLogger(__name__)


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
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [ETA: {remaining} ({rate_fmt}{postfix})]",
            ) as file_obj:
                response = requests.request(
                    method="PUT",
                    url=signed_url,
                    data=file_obj,
                    headers={"Content-Type": "application/octet-stream"},
                )
                response.raise_for_status()
        LOGGER.info(f"\nFile `{local_file_path}` upload complete\n")
    except Exception as e:
        LOGGER.error(f"Error uploading file: {e}")
        exit(1)
