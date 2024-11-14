# logic/auth_logic.py

import logging
from terralab.auth_helper import _clear_local_token
from terralab.config import CliConfig

LOGGER = logging.getLogger(__name__)


def clear_local_token():
    """Clear the local authentication token"""
    cli_config = CliConfig()  # initialize the config from environment variables
    _clear_local_token(cli_config.token_file)
    LOGGER.info("Logged out")
