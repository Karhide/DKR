"""
Remove items from your dkr config.
"""
import os
import ast
import sys
import stat
import argparse

from main import DKRConfig


def main(config, remove_entrypoints=False):
    """
    Pull the docker images specified in the config
    option parsed to this function.
    """
    current_config = DKRConfig()

    for key, value in config.items():

        if not remove_entrypoints:
            for version in value['versions']:
                current_config.remove_entrypoint_version(key, version)

        if not current_config.get_entrypoint(key).get('versions', None) or remove_entrypoints:
            current_config.remove_entrypoint(key)

    current_config.write()


def parse_arguments(argv):
    """
    Parse command-line arguments

    :param argv: command line arguments
    :return: parsed command-line arguments (argparse)
    """
    description = 'Create and add items to your dkr config.'

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-e',
                        '--remove_entrypoints',
                        action='store_true',
                        help='Remove the entrypoint passed into the config, not just the images',
                        default=False,
                        required=False)

    args = parser.parse_args()

    return args


def run_main(args=sys.argv[1:]):
    args = parse_arguments(args)

    mode = os.fstat(0).st_mode
    if not (stat.S_ISFIFO(mode) or stat.S_ISREG(mode)):
        print "dkr-remove: To use this tool, pipe in the contents of dkr-list"
        sys.exit(1)

    raw = sys.stdin.read()
    config = ast.literal_eval(raw)

    return main(config, args.remove_entrypoints)


if __name__ == '__main__':
    run_main()
