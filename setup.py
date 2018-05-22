from setuptools import setup
from dkr import __version__

MODULE_NAME='dckr'

setup(
    name=MODULE_NAME,
    version=__version__,
    description='A convenient interface to dockerised command line tools',
    zip_safe=False,
    install_requires=[
        'docker',
        'requests',
        'tabulate',
        'pyyaml',
        'natsort'
    ],
    packages=[MODULE_NAME, MODULE_NAME + '/registries'],
    entry_points={"console_scripts": [
        'dkr = dkr.main:run_main',
        'dkr-search = dkr.search:run_main',
        'dkr-list = dkr.list:run_main',
        'dkr-add = dkr.add:run_main',
        'dkr-remove = dkr.remove:run_main',
        'dkr-pull = dkr.pull:run_main',
        'dkr_comp = dkr.dkr_comp:run_main',
        'dkr-debug = dkr.debug:run_main']}
)
