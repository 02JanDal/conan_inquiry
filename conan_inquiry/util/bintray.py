"""Utility functions related to the Bintray API"""

import os
from datetime import timedelta

from requests import Session
from requests.auth import HTTPBasicAuth

from conan_inquiry.util.cache import Cache


class BintrayRateLimitExceeded(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class Bintray:
    """Simple Bintray API client"""

    def __init__(self):
        self.auth = HTTPBasicAuth(os.getenv('BINTRAY_USERNAME'), os.getenv('BINTRAY_API_KEY'))
        self.http = Session()
        self.rate = dict(limit=None, remaining=None)

    def _get(self, path):
        response = self.http.get('https://api.bintray.com/api/v1' + path, auth=self.auth)
        if 'x-ratelimit-limit' in response.headers:
            self.rate['limit'] = response.headers['x-ratelimit-limit']
            self.rate['remaining'] = response.headers['x-ratelimit-remaining']
        if response.status_code == 403 and 'exceeded your API call limit' in response.text:
            raise BintrayRateLimitExceeded('Bintray rate limit exceeded')
        return response.json()

    def get(self, path, maxage=timedelta(days=2)):
        """Issue a GET request to the Bintray API and return the parsed reponse"""
        return Cache.current_cache.get(path, maxage, 'bintray',
                                       lambda: self._get(path))

    def download_url(self, subjectrepo, path):
        """Construct a Bintray download URL"""
        return 'https://dl.bintray.com/' + subjectrepo + '/' + path

    def load_licenses(self):
        """Retrieve the list of known licenses"""
        return self.get('/licenses/oss_licenses', maxage=timedelta(days=7))
