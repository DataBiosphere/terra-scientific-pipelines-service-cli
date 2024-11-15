# client.py

import logging

from teaspoons_client import Configuration, ApiClient
from terralab.config import CliConfig
from terralab.auth_helper import (
    _load_local_token,
    _save_local_token,
    get_tokens_with_browser_open,
    refresh_tokens,
)


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
        # note that this load function by default only returns valid tokens
        access_token = _load_local_token(cli_config.token_file)
        refresh_token = _load_local_token(cli_config.refresh_file, validate=False)

        if access_token:
            LOGGER.debug(f"Found access token {access_token[-5:]}")
        if refresh_token:
            LOGGER.debug(f"Found refresh token {refresh_token[-5:]}")

        # first check if the access_token is present and valid
        if not (access_token):
            # next check the refresh token
            if refresh_token:
                # found a refresh token, try to get a new access token
                LOGGER.debug("Attempting to refresh tokens")
                try:
                    access_token, refresh_token = refresh_tokens(
                        cli_config.client_info, refresh_token
                    )
                except Exception as e:
                    LOGGER.debug(
                        f"Error refreshing tokens ({e}), resorting to browser login"
                    )
                    refresh_token = None

            if not (refresh_token):
                LOGGER.debug("No active access or refresh tokens found.")
                access_token, refresh_token = get_tokens_with_browser_open(
                    cli_config.client_info
                )

            _save_local_token(cli_config.token_file, access_token)
            _save_local_token(cli_config.refresh_file, refresh_token)

        return _get_api_client(access_token, cli_config.config["TEASPOONS_API_URL"])

    def __exit__(self, exc_type, exc_val, exc_tb):
        # no action needed
        pass
