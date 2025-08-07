# auth_helper.py

import base64
import logging
import os
import typing as t
import urllib
import webbrowser
from collections.abc import Callable
from prompt_toolkit import prompt

import jwt
from oauth2_cli_auth import (
    OAuth2ClientInfo,
    OAuthCallbackHttpServer,
    get_auth_url,
)
from oauth2_cli_auth._urllib_util import _load_json

from terralab.config import CliConfig

LOGGER = logging.getLogger(__name__)


def get_or_refresh_access_token(cli_config: CliConfig) -> str:
    """
    Check for a valid access token; if one exists, return it.

    Otherwise, check for a refresh token; if one exists, attempt to get and save new tokens, and return the access token.

    If refresh attempt fails or if no refresh token is found, prompt user to login via browser, get and save access and refresh tokens, and return the access token.

    Returns a valid access token"""
    """Get a valid access token, refreshing or obtaining a new one if necessary."""

    # check for an oauth access token file
    oauth_access_token = _load_local_token(
        cli_config.oauth_access_token_file, validate=False
    )  # oauth tokens can't be validated against b2c
    if oauth_access_token:
        LOGGER.debug("Found oauth access token")
        return oauth_access_token

    existing_access_token = _load_local_token(
        cli_config.access_token_file
    )  # note that this load function by default only returns valid tokens
    if existing_access_token:
        return existing_access_token

    existing_refresh_token = _load_local_token(
        cli_config.refresh_token_file, validate=False
    )  # refresh tokens cannot be validated
    new_refresh_token = None
    if existing_refresh_token:
        try:
            LOGGER.debug("Attempting to refresh tokens")
            new_access_token, new_refresh_token = refresh_tokens(
                cli_config, existing_refresh_token
            )
        except Exception as e:
            LOGGER.debug(f"Token refresh failed: {e}")

    if not new_refresh_token:
        LOGGER.debug("Getting new tokens via browser login")
        new_access_token, new_refresh_token = get_tokens_with_browser_open(cli_config)

    _save_local_token(cli_config.access_token_file, new_access_token)
    _save_local_token(cli_config.refresh_token_file, new_refresh_token)
    return new_access_token


def get_tokens_with_custom_redirect(cli_config: CliConfig) -> tuple[str, str]:
    """
    Provides a simplified API to:

    - Open the browser with the authorization URL
    - Wait for the user to copy the authorization code back into the program
    - Get access token from code

    :param cli_config: Configuration object containing environment specific values
    :return: Access Token and Refresh Token
    """
    client_info = cli_config.client_info

    auth_url = get_auth_url(client_info, cli_config.remote_oauth_redirect_uri)
    prompt_text = f"Authentication required.  Please paste the following URL into a browser if it does not open automatically: \n\n{auth_url}\n"
    _open_browser(
        f"{auth_url}&prompt=login&brand=scientificServices", prompt_text, LOGGER.info
    )
    code = prompt(
        "Once finished, enter the verification code provided in your browser (it will be masked here): ",
        is_password=True,
        multiline=False,
    )

    try:
        response_dict = _exchange_code_for_response(client_info, code)
    except urllib.error.URLError:
        LOGGER.error(f"Failed to get tokens with code {code}")
        exit(1)

    return response_dict["access_token"], response_dict["refresh_token"]


def get_tokens_with_browser_open(cli_config: CliConfig) -> tuple[str, str]:
    """
    Note: this is overridden from the oauth2-cli-auth library to use a custom auth url

    Provides a simplified API to:

    - Spin up the callback server
    - Open the browser with the authorization URL
    - Wait for the code to arrive
    - Get access token from code

    :param cli_config: Configuration object containing environment specific values
    :return: Access Token and Refresh Token
    """
    callback_server = OAuthCallbackHttpServer(cli_config.server_port)
    client_info = cli_config.client_info

    auth_url = get_auth_url(client_info, callback_server.callback_url)
    prompt_text = "Authentication required.  Your browser should automatically open an authentication page.  If your environment does not have access to a web browser, please exit this command and run 'terralab login' first."
    _open_browser(
        f"{auth_url}&prompt=login&brand=scientificServices", prompt_text, LOGGER.info
    )
    code = callback_server.wait_for_code()
    if code is None:
        raise ValueError(
            "No code could be obtained from browser callback page.  If your environment does not have access to a web browser, run 'terralab login' first."
        )

    response_dict = _exchange_code_for_response(client_info, code)
    return response_dict["access_token"], response_dict["refresh_token"]


def _open_browser(
    url: str,
    prompt_text: str,
    print_open_browser_instruction: Callable[[str], None] | None = print,
) -> None:
    """
    Open browser using webbrowser module and show message about URL open
    Customized from oauth2_cli_auth.code_grant

    :param print_open_browser_instruction: Callback to print the instructions to open the browser. Set to None in order to supress the output.
    :param url: URL to open and display
    :param prompt_text: Text to display in the command line
    :return: None
    """
    if print_open_browser_instruction is not None:
        print_open_browser_instruction(prompt_text)
    webbrowser.open(url)


def refresh_tokens(cli_config: CliConfig, refresh_token: str) -> tuple[str, str]:
    client_info = cli_config.client_info

    response_dict = _exchange_code_for_response(
        client_info,
        refresh_token,
        grant_type="refresh_token",
    )
    return response_dict["access_token"], response_dict["refresh_token"]


def _exchange_code_for_response(
    client_info: OAuth2ClientInfo,
    code: str,
    grant_type: str = "authorization_code",
) -> dict[str, str]:
    """
    Note: this is overridden from the oauth2-cli-auth library to customize the request for use with refresh tokens.
    Exchange a code for an access token using the endpoints from client info and return the entire response

    :param client_info: Info about oauth2 client
    :param code: Code to redeem
    :param grant_type: Type of grant request (default `authorization_code`, can also be `refresh_token`)
    :return: Response from OAuth2 endpoint
    """
    # validate grant_type input. note this is not determined by user input.
    if grant_type not in ["authorization_code", "refresh_token"]:
        LOGGER.error(f"Authentication error: Unexpected grant_type {grant_type}")
        exit(1)

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic "
        + base64.b64encode(f"{client_info.client_id}:".encode()).decode(),
    }

    # see documentation at https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow#refresh-the-access-token
    code_key = "refresh_token" if grant_type == "refresh_token" else "code"
    data = {
        code_key: code,
        "grant_type": grant_type,
    }
    encoded_data = urllib.parse.urlencode(data).encode("utf-8")

    request = urllib.request.Request(
        client_info.token_url, data=encoded_data, headers=headers
    )

    json_response: dict[str, str] = _load_json(request)

    if "error" in json_response:
        # see https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow#error-response-1
        LOGGER.debug(
            f'Error in authentication flow exchanging code for response: {json_response["error"]}; error description: {json_response["error_description"]}'
        )
    else:
        LOGGER.debug("Token refresh successful")

    return json_response


def _validate_token(token: str) -> bool:
    try:
        # Attempt to read the token to ensure it is valid.  If it isn't, the file will be removed and None will be returned.
        # Note: We explicitly do not verify the signature of the token since that will be verified by the backend services.
        # This is just to ensure the token is not expired
        jwt.decode(token, options={"verify_signature": False, "verify_exp": True})
        LOGGER.debug("Token is not expired")
        return True
    except jwt.ExpiredSignatureError:
        LOGGER.debug("Token expired")
        return False
    except Exception as e:
        LOGGER.error(f"Error validating token : {e}")
        return False


def _clear_local_token(token_file: str) -> None:
    try:
        os.remove(token_file)
    except FileNotFoundError:
        LOGGER.debug("No local token found to clean up")


def _load_local_token(token_file: str, validate: bool = True) -> t.Optional[str]:
    try:
        with open(token_file, "r") as f:
            token = f.read()
            return token if not validate or _validate_token(token) else None
    except FileNotFoundError:
        _clear_local_token(token_file)
        return None


def _save_local_token(token_file: str, token: str) -> None:
    # Create the containing directory if it doesn't exist
    os.makedirs(os.path.dirname(token_file), exist_ok=True)

    descriptor = os.open(
        token_file,
        os.O_WRONLY | os.O_CREAT,
        0o600,  # equivalent of chmod 600, i.e. no access for anyone besides current user
    )
    with os.fdopen(descriptor, "w") as f:
        f.write(token)
        f.flush()
