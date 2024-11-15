# tests/commands/test_auth_commands.py

from click.testing import CliRunner
from mockito import when, verify
from terralab.commands import auth_commands


def test_logout():
    runner = CliRunner()

    when(auth_commands.auth_logic).clear_local_token()

    result = runner.invoke(auth_commands.logout)

    assert result.exit_code == 0
    verify(auth_commands.auth_logic).clear_local_token()
