# commands/auth_commands.py

import click

from terralab.logic import auth_logic


@click.command()
def logout():
    """Clear the local authentication token"""
    auth_logic.clear_local_token()
