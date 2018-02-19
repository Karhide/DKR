import requests
import json

from natsort import natsorted
from image_registry import ImageRegistry


class QuayBiocontainersRegistry(ImageRegistry):

    QUAY_IO_FIND_REPOSITORY_URL = "https://quay.io/api/v1/find/all?query={}"
    QUAY_IO_LIST_TAGS_URL = "https://quay.io/api/v1{}"

    def __init__(self):
        pass

    def query(self, name):
        return self.get_images(name)

    def send_request(self, url):
        response = requests.get(url)
        if response.ok:
            return json.loads(response.content)
        else:
            response.raise_for_status()

    def get_tags(self, name):
        return self.send_request(
            QuayBiocontainersRegistry.QUAY_IO_LIST_TAGS_URL.format(name))

    def search_repository(self, name):
        rep_list = []

        response = self.send_request(
            QuayBiocontainersRegistry.QUAY_IO_FIND_REPOSITORY_URL.format(name))
        for entry in response['results']:
            if entry['kind'] == 'repository' and 'biocontainers' in entry['href']:
                rep_list.append(self.get_tags(entry['href']))

        return rep_list

    def get_images(self, name):
        docker_images = []
        for repo in self.search_repository(name):
            repo_name = repo['name']
            repo_namespace = repo['namespace']

            for tag in natsorted(repo['tags'].values(),
                                 reverse=True,
                                 key=lambda x: x['name']):
                docker_image = {
                    'name': repo_name,
                    'provider': 'quay.io/biocontainers',
                    'tag': tag['name'],
                    'repository': "quay.io/{}/{}:{}".format(repo_namespace,
                                                            repo_name,
                                                            tag['name'])
                }
                docker_images.append(docker_image)

        return docker_images

    def name(self):
        return "quay.io/biocontainers"