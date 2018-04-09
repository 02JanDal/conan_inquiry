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

    def print(self):
        res = self.github.search_code('conanfile.py in:path path:/')
        pass

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

        # Github repos that need to be created or located on bintray:
        # https://github.com/syslandscape/syslandscape
        # https://github.com/cajun-code/sfml.conan
        # https://github.com/erikvalkering/smartref
        # https://github.com/malwoden/conan-librsync
        # https://github.com/LighthouseJ/mtn
        # https://github.com/raulbocanegra/utils
        # https://github.com/Aquaveo/xmscore
        # https://github.com/franc0is/conan-jansson
        # https://github.com/srand/stdext-uuid
        # https://github.com/db4/conan-jwasm
        # https://github.com/ulricheck/conan-librealsense
        # https://github.com/iblis-ms/conan_gmock
        # https://github.com/zacklj89/conan-CppMicroServices
        # https://github.com/nickbruun/conan-hayai
        # https://github.com/JavierJF/TabletMode
        # https://github.com/google/fruit
        # https://github.com/StiventoUser/conan-sqlpp11-connector-postgresql
        # https://github.com/wumuzi520/conan-snappy
        # https://github.com/DigitalInBlue/Celero-Conan
        # https://github.com/Trick-17/FMath
        # https://github.com/kwint/conan-gnuplot-iostream
        # https://github.com/luisnuxx/formiga
        # https://github.com/gustavokretzer88/conan-OATH-Toolkit
        # https://github.com/lightningcpp/lightningcpp
        # https://github.com/jasonbot/conan-jansson
        # https://github.com/bfierz/vcl
        # https://github.com/SverreEplov/conan-wt
        # https://github.com/jampio/jkpak
        # https://github.com/StableTec/vulkan
        # https://github.com/tmadden/alia
        # https://github.com/JavierJF/CloseApp
        # https://github.com/e3dskunkworks/conan-celero
        # https://github.com/kheaactua/conan-ffi
        # https://github.com/matlo607/conan-swig
        # https://github.com/Exiv2/exiv2
        # https://github.com/Ubitrack/component_vision_aruco
        # https://github.com/iblis-ms/conan_gbenchmark
        # https://github.com/p47r1ck7541/conan-llvm-60
        # https://github.com/StableCoder/conan-mariadb-connector

        # https://github.com/yackey/AvtecGmock # owner exists
        # https://github.com/yackey/AEF-CI # owner exists
        # https://github.com/spielhuus/avcpp # owner exists
        # https://github.com/nwoetzel/conan-omniorb # owner exists

        for a in ['inexorgame/inexor-conan', 'odant/conan', 'vuo/conan', 'squawkcpp/conan-cpp',
                  'degoodmanwilson/opensource', 'objectx/conan', 'franc0is/conan',

                  'boujee/conan', 'mdf/2out', 'impsnldavid/public-conan', 'sunxfancy/common',
                  'jacmoe/Conan', 'madebr/openrw', 'ogs/conan', 'danimtb/public-conan', 'kwallner/stable',
                  'kwallner/testing', 'dobiasd/public-conan', 'solvingj/public-conan', 'slyrisorg/SlyrisOrg',
                  'cliutils/CLI11', 'tuncb/pangea', 'mikayex/conan-packages', 'kenfred/conan-corner',
                  'p-groarke/conan-public', 'jabaa/Conan', 'blosc/Conan', 'sourcedelica/public-conan',
                  'sourcedelica/conan', 'rockdreamer/throwing_ptr', 'qtproject/conan', 'rhard/conan',
                  'tao-cpp/tao-cpp', 'bitprim/bitprim', 'yadoms/yadoms', 'enhex/enhex', 'jilabinc/conan',
                  'bisect/bisect', 'artalus/conan-public', 'alekseevx/pft', 'mbedded-ninja/LinuxCanBus',
                  'cynarakrewe/CynaraConan', 'jsee23/public', 'foxostro/PinkTopaz', 'jgsogo/conan-packages',
                  'vtpl1/conan-expat', 'vtpl1/conan-ffmpeg', 'ess-dmsc/conan', 'acdemiralp/makina',
                  'rwth-vr/conan', 'onyx/conan']:
            splitted = a.split('/')
            repos.add(BintrayRepoDescriptor(splitted[0], splitted[1]))

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
        clean_name = clean_name.replace('+', '_')
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
