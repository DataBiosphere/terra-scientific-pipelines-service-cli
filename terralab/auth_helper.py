# auth_helper.py

import jwt
import logging
import os
import webbrowser
import typing as t

import base64
import urllib
import json
import time
from urllib.error import URLError

from collections.abc import Callable

from oauth2_cli_auth import (
    OAuth2ClientInfo,
    OAuthCallbackHttpServer,
    get_auth_url,
)

from terralab.config import CliConfig
from terralab.log import add_blankline_after


LOGGER = logging.getLogger(__name__)


def get_tokens_with_browser_open(client_info: OAuth2ClientInfo) -> tuple[str, str]:
    """
    Note: this is overridden from the oauth2-cli-auth library to use a custom auth url

    Provides a simplified API to:

    - Spin up the callback server
    - Open the browser with the authorization URL
    - Wait for the code to arrive
    - Get access token from code

    :param client_info: Client Info for Oauth2 Interaction
    :param server_port: Port of the local web server to spin up
    :return: Access Token and Refresh Token
    """
    server_port = CliConfig().server_port
    callback_server = OAuthCallbackHttpServer(server_port)
    auth_url = get_auth_url(client_info, callback_server.callback_url)
    _open_browser(f"{auth_url}&prompt=login", LOGGER.info)
    code = callback_server.wait_for_code()
    if code is None:
        raise ValueError("No code could be obtained from browser callback page")
    
    response_dict = exchange_code_for_response(client_info, callback_server.callback_url, code)
    return response_dict["access_token"], response_dict["refresh_token"]


def _open_browser(
    url: str, print_open_browser_instruction: Callable[[str], None] | None = print
) -> None:
    """
    Open browser using webbrowser module and show message about URL open
    Customized from oauth2_cli_auth.code_grant

    :param print_open_browser_instruction: Callback to print the instructions to open the browser. Set to None in order to supress the output.
    :param url: URL to open and display
    :return: None
    """
    if print_open_browser_instruction is not None:
        print_open_browser_instruction(
            add_blankline_after(
                f"Authentication required.  Your browser should automatically open an authentication page.  If it doesn't, please paste the following URL into your browser:\n\n{url}"
            )
        )
    webbrowser.open(url)

def refresh_tokens(client_info: OAuth2ClientInfo, refresh_token: str) -> tuple[str, str]:
    server_port = CliConfig().server_port
    callback_server = OAuthCallbackHttpServer(server_port)

    response_dict = exchange_code_for_response(client_info, callback_server.callback_url, refresh_token, grant_type="refresh_token")
    return response_dict["access_token"], response_dict["refresh_token"]


def exchange_code_for_response(
        client_info: OAuth2ClientInfo,
        redirect_uri: str,
        code: str,
        grant_type: str = "authorization_code",
) -> dict:
    """
    Note: this is overridden from the oauth2-cli-auth library to customize the request for use with refresh tokens
    Exchange a code for an access token using the endpoints from client info and return the entire response

    :param client_info: Info about oauth2 client
    :param redirect_uri: Callback URL
    :param code: Code to redeem
    :param grant_type: Type of grant request (default `authorization_code`, can also be `refresh_token`)
    :return: Response from OAuth2 endpoint
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + base64.b64encode(f"{client_info.client_id}:".encode()).decode(),
    }

    # see documentation at https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow#refresh-the-access-token
    code_key = "code"
    if grant_type == "refresh_token":
        code_key = "refresh_token"
    data = {
        code_key: code,
        "redirect_uri": redirect_uri,
        "grant_type": grant_type,
    }
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')

    request = urllib.request.Request(client_info.token_url, data=encoded_data, headers=headers)
    json_response = _load_json(request)

    return json_response


def _load_json(url_or_request: str | urllib.request.Request) -> dict:
    with _urlopen_with_backoff(url_or_request) as response:
        response_data = response.read().decode('utf-8')
        json_response = json.loads(response_data)
    return json_response


def _urlopen_with_backoff(url, max_retries=3, base_delay=1, timeout=15):
    retries = 0

    while retries < max_retries:
        try:
            response = urllib.request.urlopen(url, timeout=timeout)
            return response
        except Exception:
            retries += 1
            delay = base_delay * (2 ** retries)
            time.sleep(delay)

    raise URLError(f"Failed to open URL after {max_retries} retries")


def _validate_token(token: str) -> bool:
    try:
        # Attempt to read the token to ensure it is valid.  If it isn't, the file will be removed and None will be returned.
        # Note: We explicitly do not verify the signature of the token since that will be verified by the backend services.
        # This is just to ensure the token is not expired
        jwt.decode(token, options={"verify_signature": False, "verify_exp": True})
        LOGGER.debug(f"Token {token[:10]} is not expired")
        return True
    except jwt.ExpiredSignatureError:
        LOGGER.debug(f"Token {token[:10]}  expired")
        return False
    except Exception as e:
        LOGGER.error(f"Error validating token {token[:10]} : {e}")
        return False


def _clear_local_token(token_file: str):
    try:
        os.remove(token_file)
    except FileNotFoundError:
        LOGGER.debug("No local token found to clean up")


def _load_local_token(token_file: str, validate: bool = True) -> t.Optional[str]:
    try:
        with open(token_file, "r") as f:
            token = f.read()
            if not(validate):
                return token
            elif _validate_token(token):
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
