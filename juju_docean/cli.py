import argparse
import sys

from juju_docean.config import Config
from juju_docean.constraints import IMAGE_MAP
from juju_docean import commands


def _default_opts(parser):
    parser.add_argument(
        "-e", "--environment", help="Juju environment to operate on")
    parser.add_argument(
        "-v", "--verbose", help="Verbose output")


def _machine_opts(parser):
    parser.add_argument("--constraints")
    parser.add_argument(
        "--series", default="precise", choices=IMAGE_MAP.keys(),
        help="OS Release for machine.")
    parser.add_argument(
        "-n", "--num-machines", type=int, default=1,
        help="Number of machines to allocate")


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
    bootstrap.set_defaults(command=commands.Bootstrap)

    add_machine = subparsers.add_parser(
        'add-machine',
        help="Add machines to an environment")
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
    destroy_environment.set_defaults(command=commands.DestroyEnvironment)

    return parser


def main():
    parser = setup_parser()
    options = parser.parse_args()
    config = Config(options)
    options.command(
        config,
        config.connect_provider(),
        config.connect_environment())


if __name__ == '__main__':
    main()
