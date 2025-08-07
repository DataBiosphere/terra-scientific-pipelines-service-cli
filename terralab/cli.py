# cli.py

import collections
import logging
from typing import Optional, MutableMapping, Any

import click

from terralab import __version__, log
from terralab.commands.auth_commands import logout, login_with_oauth, login
from terralab.commands.pipeline_runs_commands import (
    submit,
    download,
    jobs,
    details as details_jobs,
    list_command as list_jobs,
)
from terralab.commands.pipelines_commands import (
    pipelines,
    list_command as list_pipelines,
    details as details_pipelines,
)
from terralab.commands.quotas_commands import quota

# Context settings for commands, for overwriting some click defaults
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

LOGGER = logging.getLogger(__name__)


class OrderedGroup(click.Group):
    """Override class to display the commands in the order they're added in the --help output"""

    def __init__(
        self,
        name: Optional[str] = None,
        commands: Optional[MutableMapping[str, click.Command]] = None,
        **kwargs: Any
    ) -> None:
        super(OrderedGroup, self).__init__(name, commands, **kwargs)
        #: the registered subcommands by their exported names.
        self.commands = commands or collections.OrderedDict()

    def list_commands(self, ctx: click.Context) -> list[str]:
        return list(self.commands)


@click.group(context_settings=CONTEXT_SETTINGS, cls=OrderedGroup)
@click.version_option(__version__)
@click.option(
    "--debug",
    is_flag=True,
    hidden=True,  # doesn't show up in terralab --help menu
    help="DEBUG-level logging",
)
def cli(debug: bool) -> None:
    """To submit a job, run `terralab submit PIPELINE_NAME [INPUTS] --description DESCRIPTION`

    For more information about the required inputs for a pipeline, run `terralab pipelines details PIPELINE_NAME`

    To list available pipelines, run `terralab pipelines list`"""
    log.configure_logging(debug)
    LOGGER.debug(
        "Log level set to: %s", logging.getLevelName(logging.getLogger().level)
    )


# the order in which these are added determines the order in which they show up in the --help output
cli.add_command(submit)
cli.add_command(download)

# jobs
cli.add_command(jobs)
cli.add_command(list_jobs, name="  jobs list")
cli.add_command(details_jobs, name="  jobs details")

# pipelines
cli.add_command(pipelines)
# pipelines sub-commands - still need to be called with the pipelines command
cli.add_command(list_pipelines, name="  pipelines list")
cli.add_command(details_pipelines, name="  pipelines details")

cli.add_command(quota)
cli.add_command(login)
cli.add_command(logout)

cli.add_command(login_with_oauth)  # this is hidden from the help menu


if __name__ == "__main__":
    cli()
