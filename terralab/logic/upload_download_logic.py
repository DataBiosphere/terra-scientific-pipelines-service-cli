# logic/upload_download_logic.py

import logging
import requests


LOGGER = logging.getLogger(__name__)


def upload_file_with_signed_url(local_file_path, signed_url):
    """Uploads a local file using a signed URL"""
    headers = {"Content-Type": "application/octet-stream"}
    try:
        with open(local_file_path, "rb") as f:
            # TODO add progress bar
            #     file_size = os.path.getsize(local_file_path)
            # with tqdm(total=file_size, unit='B', unit_scale=True, desc=local_file_path) as pbar:
            #     def callback(monitor):
            #         pbar.update(monitor.bytes_read)

            response = requests.put(
                signed_url, headers=headers, data=f
            )  # , headers={'Content-Length': str(file_size)}, callbacks={'response': callback})

        response.raise_for_status()  # Raise an exception if the upload fails
        LOGGER.info("File uploaded successfully")
    except Exception as e:
        LOGGER.error("Error uploading file: ", e)
        exit(1)
