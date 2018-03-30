from datetime import timedelta

from dotmap import DotMap
from natsort import natsorted

from conan_inquiry.transformers.base import BaseHTTPTransformer
from conan_inquiry.util.bintray import Bintray


class BintrayTransformer(BaseHTTPTransformer):
    def __init__(self):
        super().__init__()
        self.bt = Bintray()
        self.licenses = self.bt.load_licenses()

    def license(self, name):
        return next((l for l in self.licenses if l['name'] == name), None)

    def transform(self, package):
        for recipie in package.recipies:
            if 'repo' in recipie and 'bintray' in recipie.repo:
                parts = recipie.repo.bintray.split('/')
                self._set_unless_exists(recipie, 'remote',
                                        'https://api.bintray.com/conan/' + '/'.join(parts[:2]))
                self._set_unless_exists(recipie, 'package', parts[2].split(':')[0])
                if ':' in parts[2]:
                    self._set_unless_exists(recipie, 'user', parts[2].split(':')[1])

                bt_package = self.bt.get('/packages/' + recipie.repo.bintray)
                versions = [DotMap(name=v.split(':')[0],
                                   channel=v.split(':')[1],
                                   repo=recipie.repo.bintray,
                                   remote=recipie.remote,
                                   package=recipie.package,
                                   user=recipie.user)
                            for v in bt_package['versions']]
                if 'versions' not in package:
                    package.versions = []
                package.versions.extend(versions)
                package.versions = natsorted(package.versions, key=lambda v: v.name, reverse=True)

                sites = []
                if 'vcs_url' in bt_package and bt_package['vcs_url'] is not None:
                    sites.append(bt_package['vcs_url'])
                if 'website_url' in bt_package and bt_package['website_url'] is not None:
                    sites.append(bt_package['website_url'])
                sites = [s for s in sites if '/conan-' not in s]
                for site in sites:
                    if 'github.com' in site:
                        path = site.split('/')[-2:]
                        if not path[1].startswith('conan') and not path[1].endswith('conan') and path[1]:
                            self._set_unless_exists(package.urls, 'github', '/'.join(path))
                    else:
                        self._set_unless_exists(package.urls, 'website', site)

                if 'issue_tracker_url' in bt_package and bt_package['issue_tracker_url'] is not None:
                    url = bt_package['issue_tracker_url']
                    if 'github.com/bincrafters/' not in url:
                        self._set_unless_exists(package.urls, 'issues', url)

                if 'desc' in bt_package and bt_package['desc']:
                    desc = bt_package['desc']
                    if 'conan' in desc.lower() and ('package' in desc.lower() or 'recipe' in desc.lower()):
                        pass  # Many descriptions on bintray are in the form "Conan package for..."
                    else:
                        self._set_unless_exists(package, 'description', bt_package['desc'])
                if 'labels' in bt_package:
                    if 'keywords' not in package:
                        package.keywords = []
                    package.keywords.extend(bt_package['labels'])
                if 'licenses' in bt_package:
                    self._set_unless_exists(package, 'licenses',
                                            [self.license(l) for l in bt_package['licenses']])
                if 'name' in bt_package:
                    self._set_unless_exists(package, 'name', bt_package['name'].split(':')[0])

                files = self.bt.get('/packages/' + recipie.repo.bintray + '/files')
                conanfile = next((f for f in files if f['name'] == 'conanfile.py'), None)
                if conanfile is not None:
                    self._set_unless_exists(package.files.conanfile, 'url',
                                            self.bt.download_url('/'.join(parts[:2]),
                                                                 conanfile['path']))
                    self._set_unless_exists(package.files.conanfile, 'content',
                                            self.http.get(package.files.conanfile.url).text)
        return package
