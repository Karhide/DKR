"""
Run dkr in debug mode.
"""
import sys
import logging

from main import main, logger, errprint


def parse_arguments(argv):
    """
    DKR-debug
    Like normal dkr, but with debug logging

    Usage: 'dkr base [invocation]'

    Positional Arguments
    --------------------
    > base: Can reference an image (e.g. alpine:latest) or an entrypoint in your config, e.g. ls
    > invocation: Your normal tool invocation, (e.g. ls -la or -la if base is ls)

    Keyword Arguments
    -----------------
    > -n --no_invocation: Don't really run dkr, just log the invocation and bug out
    """
    args = {}
    no_invo = any(
        [argv.pop(index) for index, arg in enumerate(argv) if arg in ['-n', '--no_invocation']])

    if not argv:
        errprint(parse_arguments.__doc__)
        sys.exit(0)

    args['base'] = argv.pop(0)
    args['invocation'] = argv
    args['no_invo'] = no_invo

    return args


def run_main(args=sys.argv[1:]):
    """
    Sets logging level, parses arguments and runs the main function.
    """
    # By default, DKR will only log errors
    logger.setLevel(logging.DEBUG)

    args = parse_arguments(args)
    main(args['base'], args['invocation'], no_launch=args['no_invo'])


if __name__ == '__main__':
    run_main()
