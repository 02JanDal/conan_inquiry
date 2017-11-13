import copy
import re
from datetime import timedelta

import nltk
import os
import requests

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
                content=self.cache.get(package.urls.readme, timedelta(days=1),
                                       'rendered_readme',
                                       lambda: render_readme(package.urls.readme,
                                                             self.http.get(package.urls.readme).text,
                                                             '/'.join(package.urls.readme.split('/')[:-1])))
            )
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
