# logic/service_logic.py

import logging

from teaspoons_client import PublicApi, VersionProperties

from terralab.client import ClientWrapper

LOGGER = logging.getLogger(__name__)


def get_version() -> VersionProperties:
    """Get Teaspoons service version"""
    with ClientWrapper(authenticated=False) as api_client:
        public_client = PublicApi(api_client=api_client)
        return public_client.get_version()


def get_status() -> str:
    """Get the status of the Teaspoons service.
    Returns a string response summarizing the status."""
    with ClientWrapper(authenticated=False) as api_client:
        public_client = PublicApi(api_client=api_client)
        response = public_client.get_status_with_http_info()  # to get the status code

        if response.status_code == 200:
            return "Running"
        else:
            return response.data
