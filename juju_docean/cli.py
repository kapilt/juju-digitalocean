import argparse
import logging
import sys

from juju_docean.config import Config
from juju_docean.constraints import SERIES_MAP
from juju_docean.exceptions import (
    ConfigError, PrecheckError, ProviderAPIError)
from juju_docean import commands


def _default_opts(parser):
    parser.add_argument(
        "-e", "--environment", help="Juju environment to operate on")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output")


def _machine_opts(parser):
    parser.add_argument(
        "--constraints", default="",
        help="Machine allocation criteria")
    parser.add_argument(
        "--series", default="precise", choices=SERIES_MAP.values(),
        help="OS Release for machine.")


PLUGIN_DESCRIPTION = "Juju Digital Ocean client-side provider"


def setup_parser():
    if '--description' in sys.argv:
        print(PLUGIN_DESCRIPTION)
        sys.exit(0)

    parser = argparse.ArgumentParser(description=PLUGIN_DESCRIPTION)
    subparsers = parser.add_subparsers()
    bootstrap = subparsers.add_parser(
        'bootstrap',
        help="Bootstrap an environment")
    _default_opts(bootstrap)
    _machine_opts(bootstrap)
    bootstrap.add_argument(
        "--upload-tools",
        action="store_true", default=False,
        help="upload local version of tools before bootstrapping")
    bootstrap.set_defaults(command=commands.Bootstrap)

    add_machine = subparsers.add_parser(
        'add-machine',
        help="Add machines to an environment")
    add_machine.add_argument(
        "-n", "--num-machines", type=int, default=1,
        help="Number of machines to allocate")
    _default_opts(add_machine)
    _machine_opts(add_machine)
    add_machine.set_defaults(command=commands.AddMachine)

    terminate_machine = subparsers.add_parser(
        "terminate-machine",
        help="Terminate machine")
    terminate_machine.add_argument("machines", nargs="+")
    _default_opts(terminate_machine)
    terminate_machine.set_defaults(command=commands.TerminateMachine)

    destroy_environment = subparsers.add_parser(
        'destroy-environment',
        help="Destroy all machines in juju environment")
    _default_opts(destroy_environment)
#    destroy_environment.add_argument(
#        "--force", action="store_true", default=False,
#        help="Irrespective of environment state, destroy all env machines")
    destroy_environment.set_defaults(command=commands.DestroyEnvironment)

    return parser


def main():
    parser = setup_parser()
    options = parser.parse_args()
    config = Config(options)

    if config.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        datefmt="%Y/%m/%d %H:%M.%S",
        format="%(asctime)s:%(levelname)s %(message)s")
    logging.getLogger('requests').setLevel(level=logging.WARNING)

    try:
        config.validate()
    except ConfigError, e:
        print("Configuration error: %s" % str(e))
        sys.exit(1)

    cmd = options.command(
        config,
        config.connect_provider(),
        config.connect_environment())
    try:
        cmd.run()
    except ProviderAPIError, e:
        print("Provider interaction error: %s" % str(e))
    except ConfigError, e:
        print("Configuration error: %s" % str(e))
        sys.exit(1)
    except PrecheckError, e:
        print("Precheck error: %s" % str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()
