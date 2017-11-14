import logging
import os

import requests
import yaml

from conan_inquiry.util.general import load_packages, packages_directory


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
    def __init__(self):
        self.http = requests.session()
        self.packages = load_packages()
        self.existing_repos = [r['repo']['bintray']
                               for p in self.packages
                               for r in p['recipies']]

    def _gather_repos(self):
        repos = set()
        for pkg in self.packages:
            for recipie in pkg['recipies']:
                repos.add(tuple(recipie['repo']['bintray'].split('/')[:2]))
        return repos

    def _find_packages(self, repos):
        return [(owner, subject, p['name'])
                for owner, subject in repos
                for p in self.http.get('https://api.bintray.com/repos/' + owner + '/' + subject + '/packages').json()]

    def _filter_missing_repo(self, packages):
        return [p
                for p in packages
                if '/'.join(p) not in self.existing_repos]

    def _filter_missing_package(self, packages):
        return [p
                for p in packages
                if not os.path.exists(os.path.join(packages_directory(), p[2].split(':')[0].lower().replace('conan-', '') + '.yaml'))]

    def run(self):
        found = self._find_packages(self._gather_repos())
        missing_repo = self._filter_missing_repo(found)
        missing_package = self._filter_missing_package(found)
        return missing_repo, missing_package

    def print(self):
        missing_repo, missing_package = self.run()
        for repo in missing_repo:
            print('Missing repo:', '/'.join(repo))
        for pkg in missing_package:
            print('Missing package:', '/'.join(pkg))

    def generate_stubs(self):
        for name in self._find_packages():
            # pkg = self.http.get(self.url + '/' + name).json()
            clean_name = name.split(':')[0]
            fname = os.path.join(packages_directory(), clean_name.lower() + '.yaml')
            if not os.path.exists(fname):
                logging.getLogger(__name__).info('Found %s', clean_name)
                with open(fname, 'w') as f:
                    yaml.dump(dict(
                        recipies=[
                            dict(repo=dict(bintray=self.owner + '/' + self.subject + '/' + name))
                        ],
                        urls=dict()
                    ), f)
