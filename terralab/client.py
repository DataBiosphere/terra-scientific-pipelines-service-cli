# client.py

import logging

from teaspoons_client import Configuration, ApiClient
from terralab.config import CliConfig
from terralab.auth_helper import get_or_refresh_access_token


LOGGER = logging.getLogger(__name__)


def _get_api_client(token: str, api_url: str) -> ApiClient:
    api_config = Configuration()
    api_config.host = api_url
    api_config.access_token = token
    return ApiClient(configuration=api_config)


class ClientWrapper:
    """
    Wrapper to ensure that the user is authenticated before running the callback and that provides the low level api client to be used
    by subsequent commands
    """

    def __enter__(self):
        cli_config = CliConfig()  # initialize the config from environment variables

        access_token = get_or_refresh_access_token(cli_config)

        return _get_api_client(access_token, cli_config.config["TEASPOONS_API_URL"])

    def __exit__(self, exc_type, exc_val, exc_tb):
        # no action needed
        pass
