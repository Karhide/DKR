#!/usr/bin/env python
import os
import sys
import yaml
import signal
import docker
import logging
import subprocess

from tabulate import tabulate
from docker.errors import APIError

HOME = os.path.expanduser('~')
CONFIG_FILE = os.path.join(HOME, '.dkr')
DOCKER_IMAGE_VERSION_DELIM = ':'

ACTIVE_CONTAINER = None

logger = logging.getLogger()
logger_stderr_handler = logging.StreamHandler(sys.stderr)
logger.addHandler(logger_stderr_handler)


def errprint(*args, **kwargs):
    """
    Prints, but to stderr
    """
    sys.stderr.write(*args, **kwargs)
    sys.stderr.write('\n')


def print_tabulate(headers, rows, print_total_rows=True):
    """
    Pretty prints your headers and rows.
    Header length must match row length.

    :param headers: Array containing table headers
    :param rows: Array containing table row contents
    :param errprint_total_rows: Print how many rows there are.
    """
    content = rows or ['' for header in headers]
    print('\n' + tabulate(content, headers=headers))

    if print_total_rows:
        print('\nTotal %s' % len(rows))


def signal_handler(signal, frame):
    """
    Used to interrupt SIGINT and kill the active container, if one is set.
    """
    if ACTIVE_CONTAINER:
        shutdown(ACTIVE_CONTAINER)


def merge_two_dicts(x, y):
    """
    Given two dicts, merge them into a new dict as a shallow copy.
    """
    z = x.copy()
    z.update(y)
    return z


def shutdown(container):
    """
    Its the double-fork-pirouette method for rapidly killing the
    main process and returning control to the user once they have sent SIGINT, whilst making
    sure the grand-child of the main process cleanly disposes of the docker container.
    """
    try:
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)

    except OSError as e:
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    try:
        container.stop()
        container.remove()
    except APIError:
        pass


def get_image_tagged_version(image):
    """
    Tries to detect whether or not the string representing the image
    specified a version, returns True if a version is detected, or False if not.
    """
    if '/' in image:
        _, image = os.path.split(image)

    name_version = image.split(DOCKER_IMAGE_VERSION_DELIM)

    if len(name_version) > 1:
        return name_version[1]

    return None


def set_image_tagged_version(image, version='latest'):
    """
    Appends the given version to the image
    """
    return DOCKER_IMAGE_VERSION_DELIM.join([image, version])


def match_to_image_tag(client, image):
    image_tags = [tag for img in client.images.list() for tag in img.tags]

    for tag in image_tags:
        if image is tag:
            return tag

    if '/' in image:
        _, image = os.path.split(image)

    for tag in image_tags:
        if tag.endswith(image):
            return tag

    return None


def filter_local_image_tags(client, tags):
    found_images = []

    for image in client.images.list():
        for tag in tags:
            if tag in image.tags:
                found_images.append(tag)

    return list(set(found_images))


def pull_docker_image(image):
    try:
        subprocess.Popen(
            ['docker', 'pull', image],
            stdin=sys.stdin,
            stdout=sys.stderr,
            stderr=sys.stderr).wait()
    except docker.errors.ImageNotFound:
        logger.warning('Could not pull docker image, please check the URI.')


class DKRConfig:
    """
    Contains a set of methods for working with the DKR config.
    An entry in the config has the following structure, e.g. for a given 'entrypoint' bwa:

    bwa:
      versions:
        - git.oxfordnanolabs.local::4567/metrichor-bio/whalepod/bwa:latest
        - git.oxfordnanolabs.local::4567/metrichor-bio/whalepod/bwa:2.25.0--2
        - quay.io/biocontainers/bwa:latest

    The 'versions' key contains a list of references to docker images which must be usable by
    the docker client. DKR defaults to using the image that is top of the list.

    To use a version other than the default, the user should use the following syntax:
        'dkr bwa::quay.io/biocontainers/bwa:latest mem etc...'

    DKR's autocomplete functionality can assist the user in selecting an alternative version.
    """
    ENTRYPOINT_DELIM = '::'
    DEFAULT_ENTRYPOINT_VERSION = 'latest'

    def __init__(self, path=CONFIG_FILE, auto_load=True):
        """
        Initialises an instance of Config.

        :param auto: If true (default value), the file at self.path is loaded, validated and
        set to self.config if validation is passed.
        """
        self.path = path
        self.config = {}

        if auto_load:
            self.config = self.validate(config=self.load())

    def load(self):
        """
        Attempts to load the contents of the file at self.path, if any exists.
        Tries to pass the file as YAML and returns its contents.

        :return: the contents of the file at self.path
        """
        if not os.path.exists(self.path):
            return

        with open(self.path, 'r') as stream:
            return yaml.load(stream)

    def validate(self, config=None):
        """
        Validates the config passed to it by checking that each entry is unique and contains
        a key named 'versions' which is not empty.

        :param config: Optionally specify an object to validate, uses self.config if None
        :return: validated config
        """
        if not config:
            config = self.config

        all_entrypoints = []

        for key, value in config.items():
            # Check that each image has 'versions'
            versions = value.get('versions', [])
            if not versions:
                raise KeyError('Entrypoint %s has no images/versions assigned' % key)

            # Check that each entrypoint is unique
            if key in all_entrypoints:
                raise ValueError('Duplicate entrypoint found, %s' % key)

            all_entrypoints.append(key)

        return config

    def get_config(self):
        """
        Getter for config

        :return: The current value of self.config
        """
        return self.config

    def set_config(self, value):
        """
        Setter for config

        Checks whether or not the value supplied is valid before setting it,
        raises exception if it is not.

        :param value: The value to set to self.config
        """
        try:
            self.validate(config=value)
        except (KeyError, ValueError) as e:
            print("Config not set, encountered error %s" % e.msg)

        self.config = value

    config = property(get_config, set_config)

    def create(self):
        """
        Creates a file at self.path if one does not already exist

        :return: True if a file has been created, otherwise False
        """
        if not os.path.exists(self.path):
            cfg = open(self.path, 'wb+')
            cfg.close()

            return True
        return False

    def write(self, create=False):
        """
        Write the contents of self.config to file at self.path
        """
        if not os.path.exists(self.path) and not create:
            logger.error('Cannot write to non-existent config file')
            return

        if create:
            self.create()

        with open(self.path, 'wb+') as cf:
            yaml.dump(self.config, cf, default_flow_style=False)

    @staticmethod
    def split_entrypoint(entrypoint, delimeter=ENTRYPOINT_DELIM):
        """
        Splits the given string by delimeter and returns the result
        """
        return entrypoint.split(delimeter)

    @staticmethod
    def join_entrypoint(name, version, delimeter=ENTRYPOINT_DELIM):
        """
        Joins the given string by delimeter and returns the result
        """
        return delimeter.join([name, version])

    def get_entrypoint(self, entrypoint):
        """
        Gets the specified entrypoint from self.config

        :param entrypoint: Name of the desired entrypoint
        :return: The entrypoint if found, otherwise None
        """
        if not self.config:
            logger.debug('Cannot get an entrypoint from an empty config')
            return

        try:
            return self.config.get(entrypoint, None)
        except AttributeError:
            return None, None

    def add_entrypoint(self, entrypoint, versions, override_existing=False):
        """
        Adds the entrypoint with the specified default to self.config

        :param entrypoint: Name of the entrypoint to add
        :param versions: List of docker images to add
        :param override_existing: Replaces an entrypoint of the same name, if one exists
        """
        if not self.config:
            self.config = {}

        if (entrypoint not in self.config) or override_existing:
            self.config[entrypoint] = {'versions': versions}
            return

    def remove_entrypoint(self, entrypoint):
        """
        Removes the specified entrypoint from the config, if it exists

        :param entrypoint: Name of the entrypoint to remove
        """
        if not self.config:
            logger.error('Cannot remove an entrypoint from an empty config')
            return

        self.config.pop(entrypoint, None)

    def add_entrypoint_version(self, entrypoint, version, default=False):
        """
        Adds a new version to an entrypoint, if it doesn't already exist.

        :param entrypoint: The entrypoint to which the version should be added
        :param version: The new version to add
        :param default: If true, adds the new version to the top of the list
        """
        new_config = self.config
        entrypoint_val = self.get_entrypoint(entrypoint)

        if not entrypoint_val:
            logger.error('Cannot add version to non-existent entrypoint')
            return

        versions = entrypoint_val.get('versions', [])

        if version in versions:
            logger.error('Version already exists for entrypoint')
            return

        versions = [version] + versions if default else versions + [version]
        new_config[entrypoint]['versions'] = versions

        if self.validate(config=new_config):
            self.config = new_config

    def remove_entrypoint_version(self, entrypoint, version):
        """
        Removes a version from an entrypoint, as long as it actually exists.

        :param entrypoint: The entrypoint from which the version should be removed
        :param version: The version to remove
        """
        new_config = self.config
        entrypoint_val = self.get_entrypoint(entrypoint)

        if not entrypoint_val:
            logger.error('Cannot add version to non-existent entrypoint')
            return

        versions = entrypoint_val.get('versions', [])

        if version not in versions:
            logger.error('Cannot remove version which doesnt exist')
            return

        versions = [v for v in versions if v != version]
        new_config[entrypoint]['versions'] = versions

        if self.validate(config=new_config):
            self.config = new_config

    def get_entrypoint_default_version(self, entrypoint):
        """
        Gets the default, i.e. the first list item, in the list
        of versions assigned to an entrypoint

        :param entrypoint: The entrypoint for which to get the default
        :return: The default version or None
        """
        entrypoint_val = self.get_entrypoint(entrypoint)

        if entrypoint_val and entrypoint_val.get('versions', []):
            return entrypoint_val['versions'][0]

        logger.debug('Entrypoint does not exist or has no versions')
        return None

    # TODO: Get rid of this complete nonsense
    def serialise(self, config):
        """
        Transforms the config into a list format with indices,
        primarily to facilitate user interaction with the config
        """
        serialised_config = []

        self.validate(config)

        for index, item in enumerate(config.items(), start=1):
            serialised_config.append([index, item[0], item[1]['versions']])

        return serialised_config

    # TODO: And this
    def deserialise(self, config):
        """
        Transforms the serialised config back into its default format
        """
        deserialised_config = {}

        for entrypoint in config:
            deserialised_config[entrypoint[1]] = {
                'versions': entrypoint[2]
            }

        self.validate(deserialised_config)

        return deserialised_config


class DKRContainer:
    """
    Methods for preparing, initialising and executing instructions in a docker container
    for use by DKR
    """
    DEFAULT_MAPPINGS = [os.getcwd(), HOME]

    def __init__(self, image, invocation, flags, auto_prepare=True):
        """
        Initialises a Command instance.
        """
        self.client = docker.from_env()
        self.container = None

        if auto_prepare:
            self.image = self._prepare_image(image)
            self.volumes = self._prepare_volumes(invocation, *self.DEFAULT_MAPPINGS)
            self.invocation = self._prepare_invocation(invocation, self.volumes)
            self.flags = flags
            self.environment = self._prepare_environment()
            self.working_directory = self._prepare_working_directory()
            self.user = self._prepare_user()

            logger.debug('DKR-DEBUG')
            logger.debug(self.image)
            logger.debug(self.volumes)
            logger.debug(self.invocation)
            logger.debug(self.environment)
            logger.debug(self.working_directory)
            logger.debug(self.user)

    def launch_container(self):
        """
        Calls all of the methods to prepare and launch a docker container based
        on the specified image and subsequently executes the invocation on it.

        :param image: The image to base the container on
        :param invocation: The command to be executed on the docker container
        """
        self.container = self._launch_container(
            self.client,
            self.image,
            self.volumes,
            self.environment,
            self.working_directory,
            self.user
        )

        return self.container

    @staticmethod
    def _launch_container(client, image, volumes, environment, working_directory, user):
        """
        Utilises dockerpy to create an active container which will sit
        idle until used or terminated.

        :param image: Sets the image on which to base the container
        :param volumes: Sets the volumes to be mounted to the container
        :param environment: Sets the environment variables in the container
        :param working_directory: Sets the working directory in the container
        :param user: Sets the user mapping in the container
        :return: Dockerpy container object
        """
        try:
            container = client.containers.run(
                detach=True,
                auto_remove=False,
                stdin_open=True,
                image=image,
                volumes=volumes,
                working_dir=working_directory,
                environment=environment,
                user=user
            )
        except docker.errors.ImageNotFound:
            logger.error('Could not pull docker image, it might not exist.')
            sys.exit(0)

        return container

    def execute_command(self):
        rt = self._execute_command(self.container.id, self.invocation, flags=self.flags)

        return rt

    @staticmethod
    def _execute_command(container_id, invocation, flags=None):
        """
        Invokes a docker exec command via subprocess on the docker container with an id
        matching container_id.

        :param container_id: id of the container on which to execute the docker exec command
        :param invocation: array of arguments constituting the command to execute
        :return: subprocess command exit status
        """
        flags = flags or ['-i']

        command = ['docker', 'exec'] + flags + [container_id] + invocation
        rt = subprocess.Popen(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr).wait()

        return rt

    # Launch preparation methods
    def _prepare_volumes(self, paths, *default_mappings):
        """
        Algorithm for preparing the volumes required for
        mounting within the docker container
        """
        to_map = list(default_mappings) or []

        for path in paths:
            extant_path = self.__find_closest_path_to_string(path)
            if extant_path:
                # TODO: Make this much smarter, yield the enclosing dir only when needed, if possible
                to_map.extend([os.path.abspath(extant_path), os.path.abspath(os.path.dirname(extant_path))])

        return self._make_mappings(to_map)

    def _prepare_environment(self):
        """
        Returns a mapping for the HOME environment variable
        """
        env = {'HOME': self._make_mapping(HOME)}

        return env

    def _prepare_user(self):
        """
        Returns a user mapping in string format
        """
        return "{}:{}".format(os.getuid(), os.getgid())

    def _prepare_working_directory(self):
        """
        Returns a mapping for the present working directory
        """
        pwd = self._make_mapping(os.getcwd())[os.getcwd()]['bind']

        return pwd

    def _prepare_invocation(self, invocation, volumes):
        """
        Updates the invocation to use the mount points for any paths.

        Returns a  for the specified container to
        be consumed by subprocess.Popen
        """
        for index, item in enumerate(invocation):
            if item in volumes:
                item = volumes[item]['bind']
            invocation[index] = item

        return invocation

    def _prepare_image(self, image):
        """
        Pulls the image if it does not exist locally
        """
        if not get_image_tagged_version(image):
            image = set_image_tagged_version(image)

        found_image = match_to_image_tag(self.client, image)

        if not found_image:
            pull_docker_image(image)
            return image

        return found_image

    def _make_mapping(self, path):
        """
        Makes a dkr and docker aware mapping for a single path
        """
        mapping = {path: {'bind': os.path.join('/dkr', path.lstrip('//')), 'mode': 'rw'}}
        return mapping

    def _make_mappings(self, paths):
        """
        For each item in the input paths, makes a mapping for it
        and returns the set of all mappings.
        """
        mappings = {}

        for path in paths:
            mapping = self._make_mapping(path)
            mappings = merge_two_dicts(mappings, mapping)

        return mappings

    def __find_closest_path_to_string(self, path):
        """
        Treats the input string as a path.

        Scans the input 'path' recursively until a valid path is found,
        which is subsequently returned.

        Returns None if no valid path is found.
        """
        if path.startswith('~'):
            path = os.path.expanduser(path)

        if path and not os.path.exists(path):
            return self.__find_closest_path_to_string(os.path.split(path)[0])
        elif path:
            return path
        else:
            return None


def main(base, invocation, flags=None):
    """
    DKR Main function.

    :param base: Entrypoint in config or otherwise docker image reference
    :param invocation: Array constituting command to be run on the docker container
    :return: return code of command run in docker container
    """
    global ACTIVE_CONTAINER

    config = DKRConfig()
    image = config.get_entrypoint_default_version(base)

    if image:
        invocation = [base] + invocation

    command = DKRContainer(image or base, invocation, flags=flags)

    container = command.launch_container()
    ACTIVE_CONTAINER = container

    signal.signal(signal.SIGINT, signal_handler)
    rt = command.execute_command()
    shutdown(container)

    return rt


def parse_arguments(argv):
    """
    DKR
    A convenient interface for using dockerised command line tools

    Usage: 'dkr base [invocation]'

    Positional Arguments
    --------------------
    > base: Can reference an image (e.g. alpine:latest) or an entrypoint in your config, e.g. ls
    > invocation: Your normal tool invocation, (e.g. ls -la or -la if base is ls)
    """
    args = {}

    if not argv:
        errprint(parse_arguments.__doc__)
        sys.exit(0)

    args['base'] = argv.pop(0)
    args['invocation'] = argv

    return args


def run_main(args=sys.argv[1:]):
    """
    Sets logging level, parses arguments and runs the main function.
    """
    # By default, DKR will only log errors
    logger.setLevel(logging.ERROR)

    args = parse_arguments(args)
    main(args['base'], args['invocation'])


if __name__ == '__main__':
    run_main()
