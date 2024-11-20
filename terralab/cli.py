# cli.py

import click
import collections
import logging
from typing import Optional, Mapping

from terralab import __version__, log
from terralab.commands.auth_commands import logout
from terralab.commands.pipelines_commands import pipelines, list, get_info
from terralab.commands.pipeline_runs_commands import submit
from terralab.commands.quotas_commands import quota

# Context settings for commands, for overwriting some click defaults
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

LOGGER = logging.getLogger(__name__)


class OrderedGroup(click.Group):
    """Override class to display the commands in the order they're added in the --help output"""

    def __init__(
        self,
        name: Optional[str] = None,
        commands: Optional[Mapping[str, click.Command]] = None,
        **kwargs
    ):
        super(OrderedGroup, self).__init__(name, commands, **kwargs)
        #: the registered subcommands by their exported names.
        self.commands = commands or collections.OrderedDict()

    def list_commands(self, ctx: click.Context) -> Mapping[str, click.Command]:
        return self.commands


@click.group(context_settings=CONTEXT_SETTINGS, cls=OrderedGroup)
@click.version_option(__version__)
@click.option(
    "--debug",
    is_flag=True,
    hidden=True,  # doesn't show up in terralab --help menu
    help="DEBUG-level logging",
)
def cli(debug):
    log.configure_logging(debug)
    LOGGER.debug(
        "Log level set to: %s", logging.getLevelName(logging.getLogger().level)
    )


# the order in which these are added determines the order in which they show up in the --help output
# submit
cli.add_command(submit)

# pipelines
cli.add_command(pipelines)
# pipelines sub-commands - still need to be called with the pipelines command
cli.add_command(list, name="  pipelines list")
cli.add_command(get_info, name="  pipelines get-info")

cli.add_command(quota)

# logout
cli.add_command(logout)


if __name__ == "__main__":
    cli()
