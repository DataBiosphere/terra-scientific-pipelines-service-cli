# commands/auth_commands.py

import click

from terralab.logic import auth_logic


@click.command()
def logout():
    """Remove access credentials"""
    auth_logic.clear_local_token()


@click.command(hidden=True)
@click.argument("token", required=True)
def login_with_oauth(token):
    """Login using oauth bearer token from gcloud"""
    auth_logic.login_with_oauth(token)
