# client.py

import logging
from typing import Any

from teaspoons_client import ApiClient, Configuration  # type: ignore[attr-defined]

from terralab.auth_helper import get_or_refresh_access_token
from terralab.config import load_config

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

    def __enter__(self) -> ApiClient:
        cli_config = load_config()  # initialize the config from environment variables

        access_token = get_or_refresh_access_token(cli_config)
        return _get_api_client(access_token, cli_config.teaspoons_api_url)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # no action needed
        pass
