import copy
import re
from datetime import timedelta

import nltk
import os
import requests
from dotmap import DotMap

from conan_inquiry.transformers.base import BaseTransformer, BaseHTTPTransformer
from conan_inquiry.util.general import render_readme


class LicenseDetectorTransformer(BaseHTTPTransformer):
    """
    If the license is a link, try to replace it by the license ID it represents
    """

    whitespace_re = re.compile(r'\w')
    replaceable_re = re.compile(r'<[^>]*>')
    # from http://emailregex.com/
    email_re = re.compile(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')
    # should match "1987", "2004", "2001-2003", "1999, 2015-2016", etc.
    year_re = re.compile(r'\b(19|20)\d\d([\d,\- ]+(19|20)\d\d)?\b')

    def __init__(self):
        # prepare data
        super().__init__()
        directory = os.path.dirname(os.path.realpath(__file__))
        self.licenses = {self._prepare_license(os.path.join(directory, f)): f.replace('.txt', '')
                         for f in os.listdir(directory)
                         if os.path.isfile(os.path.join(directory, f))}
        self.license_keys = self.licenses.keys()

    @classmethod
    def _prepare_license(cls, path):
        with open(path, 'r') as f:
            data = f.read()

        # remove "replaceables" (values you should fill in yourself)
        data = cls.replaceable_re.sub('', data)
        # remove whitespace
        data = cls.whitespace_re.sub('', data)
        # all lowercase
        data = data.lower()

        return data

    def transform(self, package):
        return package  # TODO: update this class to handle the new license format
        if 'license' in package and package.license in self.license_keys:
            return package
        if '_license_data' not in package and 'license' in package and package.license.startswith(
                'http'):
            try:
                package._license_data = self.http.get(package.license).text
            except requests.exceptions.RequestException:
                return package
        else:
            return package

        data = package._license_data
        data = self.email_re.sub('', data)
        data = self.year_re.sub('', data)
        data = self.whitespace_re.sub('', data)
        data = data.lower()

        if data in self.licenses:
            package.license = self.licenses[data]

        del package['license_data']

        return package


class AuthorCombinerTransformer(BaseTransformer):
    def transform(self, package):
        if 'authors' not in package:
            package.authors = []
        package.author = ', '.join([a.name for a in package.authors])
        return package


class ShortDescriptionTransformer(BaseTransformer):
    tag_re = re.compile(r'<[/a-z][^>]*>')
    url_re = re.compile(r'https?://\S+')

    @classmethod
    def prepare(cls):
        if not nltk.downloader._downloader.is_installed('punkt'):
            nltk.download('punkt')

    def transform(self, package):
        # first make sure we have a description
        if 'short_description' in package and package.short_description is not None and package.short_description != '':
            self._set_unless_exists(package, 'description', package.short_description)

        if 'description' not in package or package.description is None or package.description == '':
            return package
        short_descs = nltk.tokenize.sent_tokenize(package.description)
        if len(short_descs) > 0:
            self._set_unless_exists(package, 'short_description',
                                    self.tag_re.sub('', short_descs[0]))

        package.short_description = self.url_re.sub('', package.short_description)
        package.short_description = package.short_description.strip('. -')
        return package


class KeywordDuplicateEliminator(BaseTransformer):
    def transform(self, package):
        if 'keywords' in package:
            package.keywords = list(set(package.keywords))
        return package


class ReadmeFetcher(BaseHTTPTransformer):
    def transform(self, package):
        if 'readme' in package.urls and 'readme' not in package.files:
            package.files.readme = dict(
                url=package.urls.readme,
                content=self.cache.get(package.urls.readme, timedelta(days=2),
                                       'rendered_readme',
                                       lambda: render_readme(package.urls.readme,
                                                             self.http.get(package.urls.readme).text,
                                                             '/'.join(package.urls.readme.split('/')[:-1])))
            )
        return package


class CategoriesTransformer(BaseTransformer):
    VALID_PREFIX = [
        'topic.library',
        'topic.tool',
        'environment.',
        'standard.cpp',
        'standard.c',
        'status.'
    ]

    def transform(self, package):
        categories = set(package.get('categories', set()))
        for cat in categories:
            prefix = [p for p in self.VALID_PREFIX if cat.startswith(p)]
            if not prefix:
                raise ValueError('Invalid category: {}'.format(cat))

        new_categories = set()
        for cat in categories:
            parts = cat.split('.')
            for i in range(2, len(parts)+1):
                new_categories.add('.'.join(parts[0:i]))

        package.categories = sorted(new_categories)

        return package


class OfficiallityTransformer(BaseTransformer):
    def _transform_recipe(self, package, rec):
        if 'repo' not in rec or 'bintray' not in rec.repo:
            return rec

        bt_repo = rec.repo.bintray
        bt_repo_owner = bt_repo.split('/')[0]
        bt_repo_name = bt_repo.split('/')[1]

        if bt_repo_owner == 'conan' and bt_repo_name == 'conan-center':
            self._set_unless_exists(rec, 'officiallity', 'conan-center')
            return rec
        elif bt_repo_owner == 'bincrafters' and bt_repo_name == 'public-conan':
            self._set_unless_exists(rec, 'officiallity', 'major-3rdparty')
            return rec

        if 'github' in package.urls:
            github_owner = package.urls.github.split('/')[0]
            if github_owner == bt_repo_owner:
                self._set_unless_exists(rec, 'officiallity', 'author')
                return rec

        self._set_unless_exists(rec, 'officiallity', 'none')
        return rec

    def transform(self, package: DotMap) -> DotMap:
        package.recipies = [self._transform_recipe(package, rec) for rec in package.recipies]

        officiallities = [rec.officiallity for rec in package.recipies]
        for officiallity in ['conan-center', 'author', 'major-3rdparty', 'none']:
            if officiallity in officiallities:
                package.officiallity = officiallity
                break
        else:
            package.officiallity = 'none'

        return package


class RemoveTemporariesTransformer(BaseTransformer):
    """
    Remove keys starting with _, recursively
    """

    @classmethod
    def _handle_value(cls, value):
        if isinstance(value, dict):
            new_value = copy.deepcopy(value)
            for k in value.keys():
                if k.startswith('_'):
                    del new_value[k]
                else:
                    new_value[k] = cls._handle_value(new_value[k])
            return new_value
        elif isinstance(value, list):
            new_value = copy.copy(value)
            for index, v in enumerate(value):
                new_value[index] = cls._handle_value(new_value[index])
            return new_value
        else:
            return value

    def transform(self, package):
        return self._handle_value(package)


class AddEmptyTransformer(BaseTransformer):
    def transform(self, package):
        self._set_unless_exists(package, 'keywords', [])
        self._set_unless_exists(package, 'categories', [])
        self._set_unless_exists(package, 'authors', [])

        return package
