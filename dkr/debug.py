"""
Run dkr in debug mode.
"""
import sys
import signal
import logging

from main import main as dkr_main
from main import (ACTIVE_CONTAINER, DKRConfig, DKRContainer,
                  logger, errprint, shutdown, signal_handler)


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
    > -m --mode:
        'interactive': Don't really run the command, log the invocation and jump into bash
        'noinvoke': Don't really run the command, just log the invocation and bug out
    """
    args = {}
    mode = []

    for index, arg in enumerate(argv):
        if arg in ['-m', '--mode']:
            argv.pop(index)
            mode = argv.pop(index)
            break

    if not argv:
        errprint(parse_arguments.__doc__)
        sys.exit(0)

    args['base'] = argv.pop(0)
    args['invocation'] = argv
    args['mode'] = mode

    return args


def noinvoke(image, invocation):
    """
    Run dkr-debug in noinvoke mode. This mode prints the invocation without running it.
    """
    command = DKRContainer(image, invocation, flags=[])
    errprint(" ".join(command.invocation))


def interactive(image, invocation):
    """
    Run dkr-debug in noinvoke mode. This mode prints the invocation and drops the user
    into an interactive shell.
    """
    global ACTIVE_CONTAINER

    command = DKRContainer(image, invocation, flags=[])
    container = command.launch_container()
    errprint(" ".join(command.invocation))
    ACTIVE_CONTAINER = container

    signal.signal(signal.SIGINT, signal_handler)
    rt = command._execute_command(container.id, ['bash'], flags=['-t', '-i'])
    shutdown(container)

    return rt


mode_mapping = {
    'interactive': interactive,
    'noinvoke': noinvoke
}


def main(base, invocation, mode=None):
    """
    Runs dkr-debug in the correct mode, specified by the user.
    """
    if mode:
        config = DKRConfig()
        image = config.get_entrypoint_default_version(base)

        if image:
            invocation = [base] + invocation

        mode_mapping[mode](image or base, invocation)
        return

    # By default, DKR will only log errors
    logger.setLevel(logging.DEBUG)
    dkr_main(base, invocation)


def run_main(args=sys.argv[1:]):
    """
    Sets logging level, parses arguments and runs the main function.
    """
    args = parse_arguments(args)
    main(args['base'], args['invocation'], mode=args['mode'])


if __name__ == '__main__':
    run_main()
