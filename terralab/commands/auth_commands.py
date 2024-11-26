# commands/auth_commands.py

import click

from terralab.logic import auth_logic


@click.command()
def logout():
    """Remove access credentials"""
    auth_logic.clear_local_token()
