# logic/auth_logic.py

import logging

from terralab.auth_helper import _clear_local_token, _save_local_token
from terralab.config import load_config

LOGGER = logging.getLogger(__name__)


def clear_local_token() -> None:
    """Remove access credentials"""
    cli_config = load_config()  # initialize the config from environment variables
    _clear_local_token(cli_config.access_token_file)
    _clear_local_token(cli_config.refresh_token_file)
    _clear_local_token(cli_config.oauth_token_file)
    LOGGER.info("Logged out")


def login_with_oauth(token: str) -> None:
    cli_config = load_config()
    _save_local_token(cli_config.oauth_token_file, token)
    LOGGER.debug("Saved local oauth token")
