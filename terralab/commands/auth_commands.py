# commands/auth_commands.py

import click
import logging

from terralab.logic import auth_logic

LOGGER = logging.getLogger(__name__)


@click.command()
def logout() -> None:
    """Remove access credentials"""
    auth_logic.clear_local_tokens()
    LOGGER.info("Logged out")


@click.command(hidden=True)
@click.argument("token", required=True)
def login_with_oauth(token: str) -> None:
    """Login using oauth bearer token from gcloud"""
    auth_logic.login_with_oauth(token)


@click.command()
def login() -> None:
    """Login via authorization code (useful when default login flow is not possible)"""
    # first clear any existing tokens
    auth_logic.clear_local_tokens()
    auth_logic.login_with_custom_redirect()
