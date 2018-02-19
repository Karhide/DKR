"""
Pull images from your dkr config.
"""
import os
import ast
import sys
import stat

from main import pull_docker_image


def main(config):
    """
    Pull the docker images specified in the config
    option parsed to this function.
    """
    for key, value in config.items():
        for version in value['versions']:
            pull_docker_image(version)


def run_main():
    mode = os.fstat(0).st_mode
    if not (stat.S_ISFIFO(mode) or stat.S_ISREG(mode)):
        print "dkr-pull: To use this tool, pipe in the contents of dkr-list"
        sys.exit(1)

    raw = sys.stdin.read()
    config = ast.literal_eval(raw)
    return main(config)


if __name__ == '__main__':
    run_main()
