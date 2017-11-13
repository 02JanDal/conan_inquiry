import logging
import os

import requests
import yaml


class GithubFinder:
    def __init__(self, github):
        self.github = github

    def _find_files(self, file):
        return [r for r in self.github.search_code(file) if file in r.path]

    def generate_stubs(self, directory):
        for file in self._find_files('conanfile.py'):
            repo = file.repository
            fname = os.path.join(directory, repo.name.lower() + '.yaml')
            if not os.path.exists(fname):
                logging.getLogger(__name__).info('Found %s', repo.full_name)
                with open(fname, 'w') as f:
                    yaml.dump(dict(
                        name=repo.name,
                        recipies=[
                            dict(conanfile=file.url)
                        ],
                        urls=dict(github=repo.full_name)
                    ), f)


class BintrayFinder:
    def __init__(self, owner, subject):
        self.owner = owner
        self.subject = subject
        self.url = 'https://api.bintray.com/repos/' + self.owner + '/' + self.subject
        self.http = requests.session()

    def _find_packages(self):
        return [p['name'] for p in self.http.get(self.url + '/packages').json()]

    def generate_stubs(self, directory):
        for name in self._find_packages():
            # pkg = self.http.get(self.url + '/' + name).json()
            clean_name = name.split(':')[0]
            fname = os.path.join(directory, clean_name.lower() + '.yaml')
            if not os.path.exists(fname):
                logging.getLogger(__name__).info('Found %s', clean_name)
                with open(fname, 'w') as f:
                    yaml.dump(dict(
                        recipies=[
                            dict(repo=dict(bintray=self.owner + '/' + self.subject + '/' + name))
                        ],
                        urls=dict()
                    ), f)
