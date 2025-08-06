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


def test_login_with_oauth():
    runner = CliRunner()

    test_token = "fake token"

    when(auth_commands.auth_logic).login_with_oauth(test_token)

    result = runner.invoke(auth_commands.login_with_oauth, [test_token])

    assert result.exit_code == 0
    verify(auth_commands.auth_logic).login_with_oauth(test_token)


def test_login_with_oauth_no_token():
    runner = CliRunner()

    result = runner.invoke(auth_commands.login_with_oauth)

    assert result.exit_code != 0
    assert "Error: Missing argument 'TOKEN'" in result.output


def test_login():
    runner = CliRunner()

    when(auth_commands.auth_logic).login_with_custom_redirect()

    result = runner.invoke(auth_commands.login)

    assert result.exit_code == 0
    verify(auth_commands.auth_logic).login_with_custom_redirect()
