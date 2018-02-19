"""
Script for searching for docker containers to add to your config.
"""
from __future__ import print_function

import os
import sys
import stat
import argparse
import itertools

from main import print_tabulate
from requests import ConnectionError
from registries.quay_biocontainers import QuayBiocontainersRegistry

REGISTRIES = [QuayBiocontainersRegistry()]


def query(registries, query_str):
    """

    :param registries:
    :param query_str:
    :return:
    """
    search_results = []

    # Get the search results
    index = 1
    for registry in registries:
        try:
            results = registry.query(query_str)
            for result in results:
                result['id'] = index
                search_results.append(result)
                index += 1
        except ConnectionError:
            print("Warning: Could not connect to {}. Skipping.".format(
                registry.name()), file=sys.stderr)

    return search_results


def main(query_str, rows, registries, pipe):
    """

    :param query_str:
    :param rows:
    :param registries:
    :param pipe:
    :return:
    """
    # Get and filter the search results
    results = query(registries, query_str)
    results = filter(lambda x: x['id'] in rows or not rows, results)

    # If not pipe, format and print the results
    if not pipe:
        print_tabulate(
            ['', 'Name', 'Tag', 'URL', 'Registry'],
            [[sr['id'], sr['name'], sr['tag'], sr['repository'], sr['provider']] for sr in results])
        return

    # If pipe, print the results in config form
    config = {}
    for key, group in itertools.groupby(results, lambda x: x['name']):
        images = [item['repository'] for item in group]
        config[key] = {'versions': images}

    print(config)


def parse_args(argv):
    """
    Parse command-line arguments

    :param argv: command line arguments
    :return: parsed command-line arguments (argparse)
    """
    usage = "Search docker repositories"
    parser = argparse.ArgumentParser(
        description=usage,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    list_reg = ["-l", "--list-registries"]
    parser.add_argument(list_reg[0],
                        list_reg[1],
                        dest="LIST",
                        action='store_true',
                        help="List available registries.")

    # Don't do any more than we need to
    if any(arg in list_reg for arg in argv):
        for registry in REGISTRIES:
            print(registry.name())
            sys.exit(0)

    parser.add_argument("-r", "--use_registries",
                        dest='REG',
                        action='store',
                        type=str,
                        nargs="+",
                        default=[],
                        help="Search only in <REGISTRIES>")

    parser.add_argument('QUERY',
                        action='store',
                        type=str,
                        nargs=1,
                        help='Search query')

    parser.add_argument('INDEX',
                        action='store',
                        type=int,
                        nargs="*",
                        help='Select given rows')

    args = parser.parse_args(argv)

    return args


def run_main(argv=sys.argv[1:]):
    args = parse_args(argv=argv)

    pipe = stat.S_ISFIFO(os.fstat(1).st_mode)

    if not args.LIST:
        registries = [reg for reg in REGISTRIES if reg not in args.REG]
        main(args.QUERY[0], args.INDEX, registries, pipe)
        return


if __name__ == '__main__':
    run_main()
