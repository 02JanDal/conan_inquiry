import logging
import os
from collections import namedtuple
from typing import Tuple, Set

import re
import requests
import yaml

from conan_inquiry.util.bintray import Bintray
from conan_inquiry.util.general import load_packages, packages_directory


BintrayRepoDescriptor = namedtuple('BintrayRepoDescriptor', ['repoowner', 'reponame'])
BintrayPackageDescriptor = namedtuple('BintrayPackageDescriptor', ['repoowner', 'reponame', 'name', 'linked'])


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
    """Class to detect, print and generate stubs for Bintray packages"""

    def __init__(self):
        self.client = Bintray()
        self.packages = load_packages()
        self.existing_repos = [r['repo']['bintray']
                               for p in self.packages
                               for r in p['recipies']]
        self.missing_packages = []
        self.missing_repos = []

    def _gather_repos(self) -> Set[BintrayRepoDescriptor]:
        """
        Returns all repositories (tuple of repository owner and repository name) that are currently known
        """
        repos = set()
        for pkg in self.packages:
            for recipie in pkg['recipies']:
                parts = recipie['repo']['bintray'].split('/')
                repos.add(BintrayRepoDescriptor(parts[0], parts[1]))
        repos.add(BintrayRepoDescriptor('conan', 'conan-center'))
        return repos

    def _find_packages(self, repos: Set[BintrayRepoDescriptor]) -> [BintrayPackageDescriptor]:
        """
        Returns all packages in the known repositories
        """
        pkgs = [BintrayPackageDescriptor(repo.repoowner, repo.reponame, p['name'], p['linked'])
                for repo in repos
                for p in self.client.get_all('/repos/' + repo.repoowner + '/' + repo.reponame + '/packages')]

        # replace linked packages by their sources
        for index, pkg in enumerate(pkgs):
            if pkg.linked:
                bt_package = self.client.get('/packages/' + pkg.repoowner + '/' + pkg.reponame + '/' + pkg.name)
                pkgs[index] = BintrayPackageDescriptor(bt_package['owner'],
                                                       bt_package['repo'],
                                                       pkg.name,
                                                       False)

        return list(set(pkgs))

    @classmethod
    def _default_package_filename(cls, pkg: BintrayPackageDescriptor):
        clean_name = pkg.name.split(':')[0].lower().replace('conan-', '')
        clean_name = re.sub(r'^boost_', 'boost.', clean_name)
        return os.path.join(packages_directory(), clean_name + '.yaml')

    def _filter_missing_package(self, packages: [BintrayPackageDescriptor]) -> [BintrayPackageDescriptor]:
        """Only return packages for those there is no package file available currently"""
        return [p
                for p in packages
                if not os.path.exists(self._default_package_filename(p))]

    def _filter_missing_repository(self, packages: [BintrayPackageDescriptor]) -> [BintrayPackageDescriptor]:
        """Only return packages that have missing repository descriptors"""
        return [p
                for p in packages
                if '/'.join(p[:3]) not in self.existing_repos and not p.name.startswith('Boost') and p.reponame != 'conan-center']

    def run(self):
        found = self._find_packages(self._gather_repos())
        self.missing_packages = self._filter_missing_package(found)
        self.missing_repos = sorted(self._filter_missing_repository(found))

    def print(self):
        for pkg in self.missing_packages:
            print('Missing package:', '/'.join(pkg[:3]))
        for pkg in self.missing_repos:
            print('Missing repository:', '/'.join(pkg[:3]))

    def generate_stubs(self):
        for name in self.missing_packages:
            # pkg = self.http.get(self.url + '/' + name).json()
            fname = self._default_package_filename(name)
            logging.getLogger(__name__).info('Generating %s', os.path.basename(fname))
            with open(fname, 'w') as f:
                yaml.dump(dict(
                    recipies=[
                        dict(repo=dict(bintray=name.repoowner + '/' + name.reponame + '/' + name.name))
                    ],
                    urls=dict()
                ), f)
