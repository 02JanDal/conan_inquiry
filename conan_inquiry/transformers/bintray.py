from datetime import timedelta

from dotmap import DotMap

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

                # TODO fetch all available versions
                latest_version = self.bt.get(
                    '/packages/' + recipie.repo.bintray + '/versions/_latest')
                if 'name' in latest_version:
                    versions = [
                        DotMap(name=latest_version['name'].split(':')[0],
                               channel=latest_version['name'].split(':')[1])
                    ]
                    self._set_unless_exists(recipie, 'versions', versions)

                bt_package = self.bt.get('/packages/' + recipie.repo.bintray, timedelta(days=1))
                if bt_package['vcs_url'] is not None:
                    self._set_unless_exists(recipie.urls, 'website', bt_package['vcs_url'])
                if bt_package['issue_tracker_url'] is not None:
                    self._set_unless_exists(recipie.urls, 'issues', bt_package['issue_tracker_url'])
                if bt_package['website_url'] is not None:
                    self._set_unless_exists(package.urls, 'website', bt_package['website_url'])
                if 'website' in package.urls and 'github.com' in package.urls.website:
                    self._set_unless_exists(package.urls, 'github',
                                            '/'.join(package.urls.website.split('/')[-2:]))
                self._set_unless_exists(package, 'description', bt_package['desc'])
                if 'keywords' not in package:
                    package.keywords = []
                package.keywords.extend(bt_package['labels'])
                self._set_unless_exists(package, 'licenses',
                                        [self.license(l) for l in bt_package['licenses']])
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
