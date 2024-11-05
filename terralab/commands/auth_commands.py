# commands/auth_commands.py

import click

from terralab.logic import auth_logic


@click.group()
def auth():
    """Commands for authenticating to Terralab"""


@auth.command()
def login():
    """Authenticate with Terralab via browser login to Terra b2c"""
    auth_logic.check_local_token_and_fetch_if_needed()


@auth.command()
def logout():
    """Clear the local authentication token"""
    auth_logic.clear_local_token()
