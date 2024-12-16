# logic/auth_logic.py

import logging
from terralab.auth_helper import _clear_local_token, _save_local_token
from terralab.config import CliConfig

LOGGER = logging.getLogger(__name__)


def clear_local_token():
    """Remove access credentials"""
    cli_config = CliConfig()  # initialize the config from environment variables
    _clear_local_token(cli_config.access_token_file)
    _clear_local_token(cli_config.refresh_token_file)
    _clear_local_token(cli_config.oauth_token_file)
    LOGGER.info("Logged out")


def login_with_oauth(token: str):
    cli_config = CliConfig()
    _save_local_token(cli_config.oauth_token_file, token)
    LOGGER.debug("Saved local oauth token")
