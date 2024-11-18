# config.py

import logging
from importlib import resources as impresources
from pathlib import Path
from oauth2_cli_auth import OAuth2ClientInfo
from dotenv import dotenv_values


LOGGER = logging.getLogger(__name__)


class CliConfig:
    """A class to hold configuration information for the CLI"""

    def __init__(self, config_file=".terralab-cli-config", package="terralab"):
        # read values from the specified config file
        try:
            importable_config_file = impresources.files(package) / config_file
            self.config = dotenv_values(importable_config_file)
        except ModuleNotFoundError as e:
            LOGGER.error(f"Failed to load config from {package}/{config_file}: {e}")
            exit(1)
        LOGGER.debug(f"Imported config with values: {self.config}")

        self.client_info = OAuth2ClientInfo.from_oidc_endpoint(
            self.config["OAUTH_OPENID_CONFIGURATION_URI"],
            client_id=self.config["OAUTH_CLIENT_ID"],
            # including the offline_access scope is how we request a refresh token
            scopes=[f"offline_access+email+profile+{self.config['OAUTH_CLIENT_ID']}"],
        )

        self.server_port = int(self.config["SERVER_PORT"])

        self.access_token_file = (
            f'{Path.home()}/{self.config["LOCAL_STORAGE_PATH"]}/access_token'
        )

        self.refresh_token_file = (
            f'{Path.home()}/{self.config["LOCAL_STORAGE_PATH"]}/refresh_token'
        )
