# auth_helper.py

import jwt
import logging
import os
import typing as t

from oauth2_cli_auth import (
    OAuth2ClientInfo,
    OAuthCallbackHttpServer,
    get_auth_url,
    open_browser,
    exchange_code_for_access_token,
)

from config import CliConfig


LOGGER = logging.getLogger(__name__)


def get_access_token_with_browser_open(client_info: OAuth2ClientInfo) -> str:
    """
    Note: this is overridden from the oauth2-cli-auth library to use a custom auth url

    Provides a simplified API to:

    - Spin up the callback server
    - Open the browser with the authorization URL
    - Wait for the code to arrive
    - Get access token from code

    :param client_info: Client Info for Oauth2 Interaction
    :param server_port: Port of the local web server to spin up
    :return: Access Token
    """
    server_port = CliConfig().server_port
    callback_server = OAuthCallbackHttpServer(server_port)
    auth_url = get_auth_url(client_info, callback_server.callback_url)
    open_browser(f"{auth_url}&prompt=login")
    code = callback_server.wait_for_code()
    if code is None:
        raise ValueError("No code could be obtained from browser callback page")
    return exchange_code_for_access_token(
        client_info, callback_server.callback_url, code
    )


def _validate_token(token: str) -> bool:
    try:
        # Attempt to read the token to ensure it is valid.  If it isn't, the file will be removed and None will be returned.
        # Note: to simplify, not worrying about the signature of the token since that will be verified by the backend services
        # This is just to ensure the token is not expired
        jwt.decode(token, options={"verify_signature": False, "verify_exp": True})
        return True
    except jwt.ExpiredSignatureError:
        LOGGER.debug("Token expired")
        return False
    except Exception as e:
        LOGGER.error(f"Error validating token: {e}")
        return False


def _clear_local_token(token_file: str):
    try:
        os.remove(token_file)
    except FileNotFoundError:
        LOGGER.debug("No local token found to clean up")
        pass


def _load_local_token(token_file: str) -> t.Optional[str]:
    try:
        with open(token_file, "r") as f:
            token = f.read()
            if _validate_token(token):
                return token
            else:
                return None

    except FileNotFoundError:
        _clear_local_token(token_file)
        return None


def _save_local_token(token_file: str, token: str):
    # Create the containing directory if it doesn't exist
    os.makedirs(os.path.dirname(token_file), exist_ok=True)
    with open(token_file, "w") as f:
        f.write(token)
