"""
Create and add items to your dkr config.
"""
import os
import ast
import sys
import stat
import argparse

from main import DKRConfig


def main(config):
    """
    Add the specified entries in config to the dkr config.
    """
    current_config = DKRConfig()

    for key, value in config.items():

        if key in current_config.config:
            for version in value['versions']:
                current_config.add_entrypoint_version(key, version)
            continue

        current_config.add_entrypoint(key, value['versions'])

    current_config.write(create=True)


def parse_arguments(argv):
    """
    Parse command-line arguments

    :param argv: command line arguments
    :return: parsed command-line arguments (argparse)
    """
    description = 'Create and add items to your dkr config.'

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-e',
                        '--entrypoint',
                        type=str,
                        help='Specify the entrypoint to add',
                        required=True)

    parser.add_argument('-i',
                        '--image',
                        type=str,
                        nargs="*",
                        help='Specify the images to add the entrypoint',
                        required=True)

    args = parser.parse_args()

    if not args:
        parser.print_help()
        sys.exit(0)

    config = {args.entrypoint: {'versions': [image for image in args.image]}}

    return config


def parse_stdin():
    raw = sys.stdin.read()
    config = ast.literal_eval(raw)

    return config


def run_main(args=sys.argv[1:]):

    mode = os.fstat(0).st_mode
    if not args and not (stat.S_ISFIFO(mode) or stat.S_ISREG(mode)):
        print "dkr-add: Pipe in the contents or specify command line arguments. Use -h for help."
        sys.exit(1)

    if args:
        config = parse_arguments(args)
        return main(config)

    config = parse_stdin()
    return main(config)


if __name__ == '__main__':
    run_main()
