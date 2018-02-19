"""
Script for displaying the contents of the dkr config file.
"""
import os
import sys
import stat
import docker
import argparse

from main import DKRConfig, print_tabulate, filter_local_image_tags


def main(entrypoints, images, pipe):
    """
    dkr-List Main function.

    Lists the contents of the dkr config.
    Optionally filters the returned values by the entrypoints and images arguments.

    :param entrypoints: array of integers representing index values of entrypoints in the config
    :param images: array of integers representing index values of images assigned to an entrypoint
    :param pipe: boolean determining whether the tool output is being piped
    """
    headers = ['#', 'Entrypoint', 'Images']

    # Get the config
    config = DKRConfig()

    if not config.config:
        print_tabulate(headers, [])
        return

    # Serialise the config
    output = config.serialise(config.config)

    # Filter the config for selected entrypoints
    if entrypoints:
        output = filter(lambda x: x[0] in entrypoints, output)

    # Filter the config for selected images
    if images:
        for entrypoint in output:
            entrypoint[2] = [
                version for index, version in enumerate(entrypoint[2], start=1) if index in images
            ]

    # If piping, output something machine readable
    if pipe:
        print(config.deserialise(output))
        return

    # Get local tags
    client = docker.from_env()
    local_tags = filter_local_image_tags(client, [j for i in output for j in i[2]])

    # Annotate the config entries with local tags
    headers.append('Local')
    for entrypoint in output:
        entrypoint.append(
            [bool(version in local_tags) for version in entrypoint[2]]
        )

    # Adjust the config for human readability
    for entrypoint in output:
        entrypoint[2] = "\n".join(i for i in entrypoint[2])
        entrypoint[3] = "\n".join(str(i) for i in entrypoint[3])

    # Print it
    print_tabulate(headers, output)


def parse_arguments(argv):
    """
    Parse command-line arguments

    :param argv: command line arguments
    :return: parsed command-line arguments (argparse)
    """
    description = 'List items in your dkr config.'

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('ENTRYPOINT',
                        action='store',
                        type=int,
                        nargs="*",
                        help='Filter entrypoint')

    parser.add_argument('-i',
                        '--images',
                        action='store',
                        type=int,
                        nargs="*",
                        default=[],
                        help='Filter image')

    args = parser.parse_args()

    return args


def run_main(args=sys.argv[1:]):
    args = parse_arguments(args)

    pipe = stat.S_ISFIFO(os.fstat(1).st_mode)

    return main(args.ENTRYPOINT, args.images, pipe)


if __name__ == '__main__':
    run_main()
