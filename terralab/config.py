# config.py

import logging
from dataclasses import dataclass
from importlib import resources as impresources
from pathlib import Path

from dotenv import dotenv_values
from oauth2_cli_auth import OAuth2ClientInfo

LOGGER = logging.getLogger(__name__)


@dataclass
class CliConfig:
    """A class to hold configuration information for the CLI"""

    client_info: OAuth2ClientInfo
    teaspoons_api_url: str
    server_port: int
    access_token_file: str
    refresh_token_file: str
    oauth_access_token_file: str
    remote_oauth_redirect_uri: str


def load_config(
    config_file: str = ".terralab-cli-config", package: str = "terralab"
) -> CliConfig:
    # read values from the specified config file
    try:
        importable_config_file = str(impresources.files(package) / config_file)
        config = dotenv_values(importable_config_file)
    except ModuleNotFoundError as e:
        LOGGER.error(f"Failed to load config from {package}/{config_file}: {e}")
        exit(1)
    LOGGER.debug(f"Imported config with values: {config}")

    if (server_port := config.get("SERVER_PORT")) is None:
        raise RuntimeError("Expected config value for server port not found")

    if (teaspoons_api_url := config.get("TEASPOONS_API_URL")) is None:
        raise RuntimeError("Expected config value for API URL not found")

    if (remote_oauth_redirect_uri := config.get("REMOTE_OAUTH_REDIRECT_URI")) is None:
        raise RuntimeError("Expected config value for remote redirect_uri not found")

    return CliConfig(
        client_info=OAuth2ClientInfo.from_oidc_endpoint(
            config["OAUTH_OPENID_CONFIGURATION_URI"],
            client_id=config["OAUTH_CLIENT_ID"],
            # including the offline_access scope is how we request a refresh token
            scopes=[f"offline_access+email+profile+{config['OAUTH_CLIENT_ID']}"],
        ),
        teaspoons_api_url=teaspoons_api_url,
        server_port=int(server_port),
        access_token_file=f'{Path.home()}/{config["LOCAL_STORAGE_PATH"]}/access_token',
        refresh_token_file=f'{Path.home()}/{config["LOCAL_STORAGE_PATH"]}/refresh_token',
        oauth_access_token_file=f'{Path.home()}/{config["LOCAL_STORAGE_PATH"]}/oauth_access_token',
        remote_oauth_redirect_uri=remote_oauth_redirect_uri,
    )
